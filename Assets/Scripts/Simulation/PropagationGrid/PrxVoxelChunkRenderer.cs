using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Builds chunked voxel meshes colored by normalized Prx.
/// </summary>
public class PrxVoxelChunkRenderer : MonoBehaviour
{
    [Header("Source")]
    public PropagationGridSimulator simulator;

    [Header("Rendering")]
    public Material voxelMaterial;
    public int chunkSize = 10;

    [Header("Opacity")]
    public float minAlpha = 0.00f;
    public float maxAlpha = 0.50f;
    public float alphaExponent = 5;

    [Header("Visibility")]
    [Range(0f, 1f)] public float visibilityThreshold = 0f;

    List<GameObject> chunkObjects = new List<GameObject>();
    public float MinPrx { get; private set; }
    public float MaxPrx { get; private set; }
    public bool HasPrxRange { get; private set; }

    /// <summary>
    /// Finds the grid simulator if it was not assigned manually.
    /// </summary>
    void Start()
    {
        // Finds the simulator automatically if it was not assigned
        if (simulator == null)
        {
            simulator = FindFirstObjectByType<PropagationGridSimulator>();
        }
    }

    /// <summary>
    /// Rebuilds all visible voxel chunks from the simulator data.
    /// </summary>
    public void BuildChunks()
    {
        // Removes previous chunk objects
        ClearChunks();

        // Stops when the simulator is missing
        if (simulator == null)
        {
            Debug.LogError("PrxVoxelChunkRenderer: Simulator not assigned.");
            return;
        }

        // Stops when the material is missing
        if (voxelMaterial == null)
        {
            Debug.LogError("PrxVoxelChunkRenderer: Voxel material not assigned.");
            return;
        }

        // Stops when there is no voxel data
        if (simulator.voxelsData == null || simulator.voxelsData.Count == 0)
        {
            Debug.LogWarning("PrxVoxelChunkRenderer: No voxel data available.");
            return;
        }

        // Computes Prx range for normalization
        MinPrx = float.PositiveInfinity;
        MaxPrx = float.NegativeInfinity;
        HasPrxRange = false;

        // Searches all voxels to find the min and max Prx values
        for (int i = 0; i < simulator.voxelsData.Count; i++)
        {
            float value = simulator.voxelsData[i].prxDbm;

            if (value < MinPrx)
            {
                MinPrx = value;
            }

            if (value > MaxPrx)
            {
                MaxPrx = value;
            }
        }

        HasPrxRange = true;

        // Groups voxels by chunk
        Dictionary<Vector3Int, List<VoxelData>> chunks = new Dictionary<Vector3Int, List<VoxelData>>();

        // Iterates through all voxels
        List<VoxelData> voxels = simulator.voxelsData;
        for (int i = 0; i < voxels.Count; i++)
        {
            // Gets the current voxel
            VoxelData sample = voxels[i];

            // Computes which chunk contains this voxel
            Vector3Int chunkCoord = new Vector3Int(
                sample.gridX / chunkSize,
                sample.gridY / chunkSize,
                sample.gridZ / chunkSize);

            // Stores the voxel list of the current chunk
            List<VoxelData> chunkVoxelsList = null;

            // Gets the existing chunk list when available
            if (chunks.ContainsKey(chunkCoord))
            {
                chunkVoxelsList = chunks[chunkCoord];
            } // Creates a new voxel list for this chunk otherwise
            else
            {
                chunkVoxelsList = new List<VoxelData>();
                chunks.Add(chunkCoord, chunkVoxelsList);
            }

            // Adds the current voxel to its chunk
            chunkVoxelsList.Add(sample);
        }

        // Creates one mesh object per chunk
        foreach (Vector3Int chunkCoord in chunks.Keys)
        {
            List<VoxelData> chunkVoxelsList = chunks[chunkCoord];
            CreateChunkObject(chunkCoord, chunkVoxelsList, MinPrx, MaxPrx);
        }

        Debug.Log($"PrxVoxelChunkRenderer: Built {chunkObjects.Count} chunk objects.");
    }

    /// <summary>
    /// Creates one chunk object and assigns its generated mesh.
    /// </summary>
    private void CreateChunkObject(Vector3Int chunkCoord, List<VoxelData> chunkVoxelsList, float minPrx, float maxPrx)
    {
        // Builds the mesh of the chunk from its voxel list
        Mesh mesh = BuildChunkMesh(chunkVoxelsList, minPrx, maxPrx);

        // Creates one GameObject to render the chunk
        GameObject chunkObject = new GameObject($"VoxelChunk_{chunkCoord.x}_{chunkCoord.y}_{chunkCoord.z}");

        // Sets the same layer as the owner so it can be rendered by the same cameras
        chunkObject.layer = gameObject.layer;

        // Parents the chunk object to the owner of this script
        chunkObject.transform.SetParent(transform, false);

        // Adds the necessary components to render geometry
        MeshFilter meshFilter = chunkObject.AddComponent<MeshFilter>();
        MeshRenderer meshRenderer = chunkObject.AddComponent<MeshRenderer>();

        // Assigns the generated mesh to the MeshFilter
        meshFilter.sharedMesh = mesh;

        // Assigns the voxel material to the MeshRenderer
        meshRenderer.sharedMaterial = voxelMaterial;

        // Disables shadows because this is a visualization material
        meshRenderer.shadowCastingMode = ShadowCastingMode.Off;
        meshRenderer.receiveShadows = false;

        // Disables probes so they do not affect the visualization material
        meshRenderer.lightProbeUsage = LightProbeUsage.Off;
        meshRenderer.reflectionProbeUsage = ReflectionProbeUsage.Off;

        // Adds the chunk object to the list
        chunkObjects.Add(chunkObject);
    }

    /// <summary>
    /// Builds a mesh containing all visible voxels of one chunk.
    /// </summary>
    private Mesh BuildChunkMesh(List<VoxelData> samples, float minPrx, float maxPrx)
    {
        float normalizedPrx;

        // Filters visible samples based on visibility threshold
        List<VoxelData> visibleSamples = new List<VoxelData>();

        for (int i = 0; i < samples.Count; i++)
        {
            normalizedPrx = Normalize(samples[i].prxDbm, minPrx, maxPrx);

            if (normalizedPrx >= visibilityThreshold)
            {
                visibleSamples.Add(samples[i]);
            }
        }

        // 1 - Calculate the required mesh size
        // A cube uses 24 vertices: 6 faces * 4 vertices per face
        // It also uses 36 triangle indices: 6 faces * 2 triangles * 3 indices

        int cubeCount = visibleSamples.Count;
        int vertexCount = cubeCount * 24;
        int triangleIndexCount = cubeCount * 36;

        // Final mesh arrays
        Vector3[] vertices = new Vector3[vertexCount];
        Color[] colors = new Color[vertexCount];
        int[] triangles = new int[triangleIndexCount];

        // 2 - Define the 8 basic corner positions of a cube

        // Half size of the voxel used to place corners around the center
        float half = simulator.voxelSizeMeters * 0.5f;

        // Local cube corners
        Vector3[] cubeVertices = new Vector3[]
        {
            // Back face corners
            new Vector3(-half, -half, -half),
            new Vector3( half, -half, -half),
            new Vector3( half,  half, -half),
            new Vector3(-half,  half, -half),

            // Front face corners 
            new Vector3(-half, -half,  half),
            new Vector3( half, -half,  half),
            new Vector3( half,  half,  half),
            new Vector3(-half,  half,  half),
        };

        // 3 - Define which 4 basic corners form each cube face
        // The vertex order determines the outward direction of each face normal
        int[][] faces = new int[][]
        {
            new int[] { 3, 2, 1, 0 }, // Back
            new int[] { 6, 7, 4, 5 }, // Front
            new int[] { 7, 3, 0, 4 }, // Left
            new int[] { 2, 6, 5, 1 }, // Right
            new int[] { 7, 6, 2, 3 }, // Top
            new int[] { 0, 1, 5, 4 }  // Bottom
        };

        // Offsets that track positions inside the final mesh arrays
        int vertexOffset = 0;
        int triangleOffset = 0;

        // Uses the transmitter rotation to orient each voxel with the grid
        Quaternion voxelRotation = simulator.settings.transmitter.rotation;

        // 4 - Build every visible voxel from the basic cube geometry
        // Each local corner is rotated with the grid and moved to the voxel world position
        for (int i = 0; i < visibleSamples.Count; i++)
        {
            // Gets the current voxel
            VoxelData sample = visibleSamples[i];

            // Normalizes Prx
            normalizedPrx = Normalize(sample.prxDbm, minPrx, maxPrx);

            // Encodes Prx as heat color plus alpha
            Color cubeColor = EvaluateHeatColor(normalizedPrx);

            // Iterates through the 6 faces of the cube
            for (int face = 0; face < 6; face++)
            {
                // First vertex index of this face
                int faceVertexStart = vertexOffset + face * 4;

                // 5 - Duplicate the 4 required corners for each face
                // This produces the 24 independent vertices used by the final cube
                vertices[faceVertexStart + 0] = transform.InverseTransformPoint(sample.centerWorldPosition + voxelRotation * cubeVertices[faces[face][0]]);
                vertices[faceVertexStart + 1] = transform.InverseTransformPoint(sample.centerWorldPosition + voxelRotation * cubeVertices[faces[face][1]]);
                vertices[faceVertexStart + 2] = transform.InverseTransformPoint(sample.centerWorldPosition + voxelRotation * cubeVertices[faces[face][2]]);
                vertices[faceVertexStart + 3] = transform.InverseTransformPoint(sample.centerWorldPosition + voxelRotation * cubeVertices[faces[face][3]]);

                // 6 - Assign the same color to the 4 vertices of the face
                colors[faceVertexStart + 0] = cubeColor;
                colors[faceVertexStart + 1] = cubeColor;
                colors[faceVertexStart + 2] = cubeColor;
                colors[faceVertexStart + 3] = cubeColor;

                // 7 - Build the 2 triangles of the current face
                triangles[triangleOffset + 0] = faceVertexStart + 0;
                triangles[triangleOffset + 1] = faceVertexStart + 1;
                triangles[triangleOffset + 2] = faceVertexStart + 2;
                triangles[triangleOffset + 3] = faceVertexStart + 0;
                triangles[triangleOffset + 4] = faceVertexStart + 2;
                triangles[triangleOffset + 5] = faceVertexStart + 3;

                // Moves to the next face
                triangleOffset += 6;
            }

            // Moves to the next cube
            vertexOffset += 24;
        }

        // 8 - Create the Unity mesh from the generated vertices, colors, and triangle indices
        Mesh mesh = new Mesh();
        mesh.name = "PrxVoxelChunkMesh";

        // Uses 32-bit indices if the mesh exceeds the 65535 vertex limit
        mesh.indexFormat = IndexFormat.UInt32;
        mesh.vertices = vertices;
        mesh.colors = colors;
        mesh.triangles = triangles;

        // Recalculates normals and bounds
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        // Returns the generated mesh
        return mesh;
    }

    /// <summary>
    /// Normalizes one value between the selected minimum and maximum range.
    /// </summary>
    private float Normalize(float value, float minValue, float maxValue)
    {
        float range = maxValue - minValue;

        if (range <= 0.001f)
        {
            return 1f;
        }

        return Mathf.Clamp01((value - minValue) / range);
    }

    /// <summary>
    /// Deletes all generated chunk objects.
    /// </summary>
    private void ClearChunks()
    {
        for (int i = 0; i < chunkObjects.Count; i++)
        {
            if (chunkObjects[i] != null)
            {
                Destroy(chunkObjects[i]);
            }
        }

        chunkObjects.Clear();
    }

    /// <summary>
    /// Converts normalized received power into voxel color and alpha.
    /// </summary>
    private Color EvaluateHeatColor(float normalizedPrx)
    {
        normalizedPrx = Mathf.Clamp01(normalizedPrx);

        float alphaFactor = Mathf.Pow(normalizedPrx, alphaExponent);

        Color color = new Color(normalizedPrx, 0f, 0f, Mathf.Lerp(minAlpha, maxAlpha, alphaFactor));

        return color;
    }

    /// <summary>
    /// Changes the visible Prx threshold and rebuilds the chunks.
    /// </summary>
    public void SetVisibilityThreshold(float threshold)
    {
        visibilityThreshold = Mathf.Clamp01(threshold);
        BuildChunks();
    }
}
