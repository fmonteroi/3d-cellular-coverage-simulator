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

    List<GameObject> chunkObjects = new List<GameObject>();

    void Start()
    {
        // Find the simulator automatically if it was not assigned
        if (simulator == null)
        {
            simulator = FindFirstObjectByType<PropagationGridSimulator>();
        }
    }

    public void BuildChunks()
    {
        // Remove previous chunk objects
        ClearChunks();

        // Guard clauses
        if (simulator == null)
        {
            Debug.LogError("PrxVoxelChunkRenderer: Simulator not assigned.");
            return;
        }

        if (voxelMaterial == null)
        {
            Debug.LogError("PrxVoxelChunkRenderer: Voxel material not assigned.");
            return;
        }

        if (simulator.voxelsData == null || simulator.voxelsData.Count == 0)
        {
            Debug.LogWarning("PrxVoxelChunkRenderer: No voxel data available.");
            return;
        }

        // Computes Prx range for normalization
        float minPrx = float.PositiveInfinity;
        float maxPrx = float.NegativeInfinity;

        // Loops through all voxels to find the min and max Prx values
        for (int i = 0; i < simulator.voxelsData.Count; i++)
        {
            float value = simulator.voxelsData[i].prxDbm;

            if (value < minPrx)
            {
                minPrx = value;
            }

            if (value > maxPrx)
            {
                maxPrx = value;
            }
        }

        // Groups voxels by chunk
        Dictionary<Vector3Int, List<VoxelData>> chunks = new Dictionary<Vector3Int, List<VoxelData>>();

        // Loops through all voxels
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

            // Variable to store the voxel list of the current chunk
            List<VoxelData> chunkVoxelsList = null;

            // If the chunk already exists, gets its list
            if (chunks.ContainsKey(chunkCoord))
            {
                chunkVoxelsList = chunks[chunkCoord];
            } // Otherwise, creates a new voxel list for this chunk
            else
            {
                chunkVoxelsList = new List<VoxelData>();
                chunks.Add(chunkCoord, chunkVoxelsList);
            }

            // Adds the current voxel to its chunk
            chunkVoxelsList.Add(sample);
        }

        // Create one mesh object per chunk
        foreach (Vector3Int chunkCoord in chunks.Keys)
        {
            List<VoxelData> chunkVoxelsList = chunks[chunkCoord];
            CreateChunkObject(chunkCoord, chunkVoxelsList, minPrx, maxPrx);
        }

        Debug.Log($"PrxVoxelChunkRenderer: Built {chunkObjects.Count} chunk objects.");
    }

    private void CreateChunkObject(Vector3Int chunkCoord, List<VoxelData> chunkVoxelsList, float minPrx, float maxPrx)
    {
        // Builds the mesh of the chunk from its voxel list
        Mesh mesh = BuildChunkMesh(chunkVoxelsList, minPrx, maxPrx);

        // Creates one GameObject to render the chunk
        GameObject chunkObject = new GameObject($"VoxelChunk_{chunkCoord.x}_{chunkCoord.y}_{chunkCoord.z}");
        // Parents the chunk object to the owner of this script
        chunkObject.transform.SetParent(transform, false);

        // Adds the necessary components to render geometry
        MeshFilter meshFilter = chunkObject.AddComponent<MeshFilter>();
        MeshRenderer meshRenderer = chunkObject.AddComponent<MeshRenderer>();

        // Assigns the generated mesh to the MeshFilter
        meshFilter.sharedMesh = mesh;

        // Assign the voxel material to the MeshRenderer
        meshRenderer.sharedMaterial = voxelMaterial;

        // Disable shadows because it's not a lit material
        meshRenderer.shadowCastingMode = ShadowCastingMode.Off;
        meshRenderer.receiveShadows = false;

        // Disable light probes so they don't try to light the material
        meshRenderer.lightProbeUsage = LightProbeUsage.Off;
        meshRenderer.reflectionProbeUsage = ReflectionProbeUsage.Off;

        // Adds the chunk object to the list
        chunkObjects.Add(chunkObject);
    }

    private Mesh BuildChunkMesh(List<VoxelData> samples, float minPrx, float maxPrx)
    {
        // Each voxel is a cube with 6 faces, each face has 4 vertices and 2 triangles (6 indices)
        int cubeCount = samples.Count;
        int vertexCount = cubeCount * 24;
        int triangleCount = cubeCount * 36;

        // Final mesh arrays
        Vector3[] vertices = new Vector3[vertexCount];
        Color[] colors = new Color[vertexCount];
        int[] triangles = new int[triangleCount];

        // Half size of the voxel, used to place corners around the center
        float half = simulator.cellSizeMeters * 0.5f;

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

        // 6 faces, 4 vertices each from the cubeVertices array
        int[][] faces = new int[][]
        {
            new int[] { 0, 1, 2, 3 },
            new int[] { 5, 4, 7, 6 },
            new int[] { 4, 0, 3, 7 },
            new int[] { 1, 5, 6, 2 },
            new int[] { 3, 2, 6, 7 },
            new int[] { 4, 5, 1, 0 }
        };

        // Offsets to keep track of where we are in the final mesh arrays
        int vertexOffset = 0;
        int triangleOffset = 0;

        // Loops through all voxels of the chunk 
        for (int i = 0; i < samples.Count; i++)
        {
            // Gets the current voxel
            VoxelData sample = samples[i];

            // Normalizes Prx
            float normalized = Normalize(sample.prxDbm, minPrx, maxPrx);

            // Encode Prx as red intensity and alpha
            Color cubeColor = new Color(normalized, 0f, 0f, Mathf.Lerp(minAlpha, maxAlpha, normalized));

            // Converts voxel center from world space to local mesh space
            Vector3 localCenter = transform.InverseTransformPoint(sample.centerWorldPosition);

            // Loops through the 6 faces of the cube
            for (int face = 0; face < 6; face++)
            {
                // First vertex index of this face
                int faceVertexStart = vertexOffset + face * 4;

                // Build the 4 vertices of the current face
                vertices[faceVertexStart + 0] = localCenter + cubeVertices[faces[face][0]];
                vertices[faceVertexStart + 1] = localCenter + cubeVertices[faces[face][1]];
                vertices[faceVertexStart + 2] = localCenter + cubeVertices[faces[face][2]];
                vertices[faceVertexStart + 3] = localCenter + cubeVertices[faces[face][3]];

                // Assign the same color to the 4 vertices of the face
                colors[faceVertexStart + 0] = cubeColor;
                colors[faceVertexStart + 1] = cubeColor;
                colors[faceVertexStart + 2] = cubeColor;
                colors[faceVertexStart + 3] = cubeColor;

                // Build the 2 triangles of the current face
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

        // Creates the final mesh object
        Mesh mesh = new Mesh();
        mesh.name = "PrxVoxelChunkMesh";

        // Uses 32-bit indices if we exceed the 65535 vertex limit of 16-bit indices
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

    private float Normalize(float value, float minValue, float maxValue)
    {
        float range = maxValue - minValue;

        if (range <= 0.001f)
        {
            return 1f;
        }

        return Mathf.Clamp01((value - minValue) / range);
    }

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
}
