using UnityEngine;

/// <summary>
/// Builds a 3D mesh from reconstructed gain data.
/// 
/// Matrix.
///   [theta, phi].
///   theta = 0 to 180.
///   phi   = 0 to 359.
/// </summary>
[RequireComponent(typeof(MeshFilter))]
[RequireComponent(typeof(MeshRenderer))]
public class PatternGainMeshRenderer : MonoBehaviour
{
    // --------------------------------------------------
    // Input parameters
    // --------------------------------------------------

    [Header("Source")]
    public PatternGainReconstructor reconstructor;

    [Header("Geometry")]
    public float radiusScale = 1.25f;
    public float minRadius = 0.02f;

    Mesh mesh;

    /// <summary>
    /// Uses the singleton reconstructor when no source was assigned.
    /// </summary>
    void Awake()
    {
        // If the reconstructor is not assigned, uses the singleton instance
        if (reconstructor == null)
        {
            reconstructor = PatternGainReconstructor.Instance;
        }
    }

    /// <summary>
    /// Builds the initial antenna pattern mesh.
    /// </summary>
    void Start()
    {
        BuildMesh();
    }

    /// <summary>
    /// Rebuilds the mesh when Inspector values change during play mode.
    /// </summary>
    void OnValidate()
    {
        if (!Application.isPlaying)
        {
            return;
        }

        BuildMesh();
    }

    /// <summary>
    /// Clears the generated mesh when the renderer is disabled.
    /// </summary>
    void OnDisable()
    {
        MeshFilter mf = GetComponent<MeshFilter>();
        if (mf != null)
        {
            mf.sharedMesh = null;
        }


        if (mesh != null)
        {
            Destroy(mesh);
            mesh = null;
        }
    }

    /// <summary>
    /// Builds the mesh from the selected gain matrix.
    /// </summary>
    public void BuildMesh()
    {
        // Validates reconstructor
        if (reconstructor == null)
        {
            Debug.LogError("PatternGainMeshRenderer: Reconstructor not assigned.");
            return;
        }
        if (!reconstructor.IsReady)
        {
            Debug.LogError("PatternGainMeshRenderer: Reconstructor is not ready yet.");
            return;
        }

        // Gets the matrix used for geometry radius
        float[,] radiusValues = reconstructor.GainDbiMatrix;

        if (reconstructor.method == PatternGainReconstructor.ReconstructionMethod.Omni)
        {
            radiusValues = reconstructor.GainLinearMatrix;
        }

        // Keeps colors based on dBi values
        float[,] colorValues = reconstructor.GainDbiMatrix;

        int thetaCount = radiusValues.GetLength(0);
        int phiCount = radiusValues.GetLength(1);

        // Initializes min and max values for radius normalization
        float minRadiusValue = float.PositiveInfinity;
        float maxRadiusValue = float.NegativeInfinity;

        // Initializes min and max values for color normalization
        float minColorValue = float.PositiveInfinity;
        float maxColorValue = float.NegativeInfinity;

        for (int t = 0; t < thetaCount; t++)
        {
            for (int p = 0; p < phiCount; p++)
            {
                float radiusValue = radiusValues[t, p];
                float colorValue = colorValues[t, p];

                if (radiusValue < minRadiusValue)
                {
                    minRadiusValue = radiusValue;
                }

                if (radiusValue > maxRadiusValue)
                {
                    maxRadiusValue = radiusValue;
                }

                if (colorValue < minColorValue)
                {
                    minColorValue = colorValue;
                }

                if (colorValue > maxColorValue)
                {
                    maxColorValue = colorValue;
                }
            }
        }

        // Omni color uses a fixed visual range so nulls do not dominate the gradient
        if (reconstructor.method == PatternGainReconstructor.ReconstructionMethod.Omni)
        {
            minColorValue = maxColorValue - 50f;
        }

        // Creates mesh arrays
        int vertexCount = thetaCount * phiCount;
        int quadCount = (thetaCount - 1) * phiCount;

        Vector3[] vertices = new Vector3[vertexCount];
        Color[] colors = new Color[vertexCount];
        int[] triangles = new int[quadCount * 6];

        // Builds all vertices and colors
        for (int t = 0; t < thetaCount; t++)
        {
            // Convert theta from degrees to radians
            float thetaRad = t * Mathf.Deg2Rad;
            float sinTheta = Mathf.Sin(thetaRad);
            float cosTheta = Mathf.Cos(thetaRad);

            for (int p = 0; p < phiCount; p++)
            {
                // Convert phi from degrees to radians
                float phiRad = (p + 90f) * Mathf.Deg2Rad;

                // Gets vertex index
                int index = t * phiCount + p;

                // Gets radius and color values for this direction
                float radiusValue = radiusValues[t, p];
                float colorValue = colorValues[t, p];

                // Converts value into radius
                float radius = EvaluateRadius(radiusValue, minRadiusValue, maxRadiusValue);

                // Convert spherical coordinates to Cartesian coordinates
                float x = radius * sinTheta * Mathf.Cos(phiRad);
                float y = radius * cosTheta;
                float z = radius * sinTheta * Mathf.Sin(phiRad);

                vertices[index] = new Vector3(x, y, z);

                // Normalizes the value to the zero to one range for color encoding
                float normalized = Normalize01(colorValue, minColorValue, maxColorValue);

                // Stores data in vertex colors:
                // r = normalized gain
                // g = normalized theta
                // b = normalized phi
                // a = base alpha = 1
                float theta01 = t / (float)(thetaCount - 1);
                float phi01 = p / (float)(phiCount - 1);

                colors[index] = new Color(normalized, theta01, phi01, 1f);
            }
        }

        // Builds triangle indices
        int tri = 0;

        for (int t = 0; t < thetaCount - 1; t++)
        {
            for (int p = 0; p < phiCount; p++)
            {
                // Wrap phi so the mesh closes horizontally
                int pNext = (p + 1) % phiCount;

                // Get the 4 corners of the quad
                int a = t * phiCount + p;
                int b = (t + 1) * phiCount + p;
                int c = (t + 1) * phiCount + pNext;
                int d = t * phiCount + pNext;

                // First triangle
                triangles[tri++] = a;
                triangles[tri++] = c;
                triangles[tri++] = b;

                // Second triangle
                triangles[tri++] = a;
                triangles[tri++] = d;
                triangles[tri++] = c;
            }
        }

        // Creates or clears mesh
        if (mesh == null)
        {
            mesh = new Mesh();
            mesh.name = "PatternGainMesh";
        }
        else
        {
            mesh.Clear();
        }

        // Uses 32-bit indices if needed
        if (vertexCount > 65000)
        {
            mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
        }

        // Assigns mesh data
        mesh.vertices = vertices;
        mesh.colors = colors;
        mesh.triangles = triangles;

        // Recalculates normals and bounds
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        // Assigns mesh to MeshFilter
        GetComponent<MeshFilter>().sharedMesh = mesh;
    }

    // --------------------------------------------------
    // Helpers
    // --------------------------------------------------

    /// <summary>
    /// Converts a value into a radius.
    /// </summary>
    private float EvaluateRadius(float value, float minValue, float maxValue)
    {
        float normalized = Normalize01(value, minValue, maxValue);
        return Mathf.Max(minRadius, normalized * radiusScale);
    }

    /// <summary>
    /// Normalizes a value to the zero to one range.
    /// </summary>
    private float Normalize01(float value, float minValue, float maxValue)
    {
        float range = maxValue - minValue;

        if (range <= 1e-8f)
        {
            return 0f;
        }

        return Mathf.Clamp01((value - minValue) / range);
    }
}
