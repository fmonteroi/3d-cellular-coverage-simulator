using UnityEngine;

/// <summary>
/// Builds a 3D mesh from PatternGainMatrixProvider data.
/// Uses vertex colors where min = 0% red and max = 100% red.
/// </summary>
[RequireComponent(typeof(MeshFilter))]
[RequireComponent(typeof(MeshRenderer))]
public class PatternGainMeshRenderer : MonoBehaviour
{
    public enum ValueMode
    {
        Linear,
        RelativeDb,
        AbsoluteDbi
    }

    [Header("Source")]
    public PatternGainReconstructor reconstructor;

    [Header("Display mode")]
    public ValueMode valueMode = ValueMode.AbsoluteDbi;

    [Header("Geometry")]
    public float radiusScale = 1f;
    public float minRadius = 0.02f;
    public bool rebuildOnStart = true;

    [Header("Color")]
    public bool useRedGradient = true;

    [Header("Debug")]
    public bool logRange = true;

    Mesh mesh;

    void Awake()
    {
        // Auto-find provider if not assigned
        if (reconstructor == null)
            reconstructor = PatternGainReconstructor.Instance;
    }

    void Start()
    {
        if (rebuildOnStart)
            BuildMesh();
    }

    /// <summary>
    /// Rebuilds the mesh from provider data.
    /// </summary>
    public void BuildMesh()
    {
        if (reconstructor == null)
        {
            Debug.LogError("PatternGainMeshRenderer: Reconstructor not assigned and no singleton instance found.");
            return;
        }

        if (!reconstructor.IsReady)
        {
            Debug.LogError("PatternGainMeshRenderer: Reconstructor is not ready yet.");
            return;
        }

        float[,] values = GetSelectedMatrix();
        int thetaCount = values.GetLength(0); // expected 181
        int phiCount = values.GetLength(1);   // expected 360

        float minValue = float.PositiveInfinity;
        float maxValue = float.NegativeInfinity;

        // Find range for color mapping
        for (int t = 0; t < thetaCount; t++)
        {
            for (int p = 0; p < phiCount; p++)
            {
                float v = values[t, p];
                if (v < minValue) minValue = v;
                if (v > maxValue) maxValue = v;
            }
        }

        if (logRange)
            Debug.Log($"PatternGainMeshRenderer: mode={valueMode}, min={minValue}, max={maxValue}");

        int vertexCount = thetaCount * phiCount;
        Vector3[] vertices = new Vector3[vertexCount];
        Color[] colors = new Color[vertexCount];
        Vector2[] uvs = new Vector2[vertexCount];

        // Two triangles per quad
        int quadCount = (thetaCount - 1) * phiCount;
        int[] triangles = new int[quadCount * 6];

        // Build vertices
        for (int t = 0; t < thetaCount; t++)
        {
            float thetaDeg = t;
            float thetaRad = thetaDeg * Mathf.Deg2Rad;

            for (int p = 0; p < phiCount; p++)
            {
                float phiDeg = p;
                float phiRad = (phiDeg + 90f) * Mathf.Deg2Rad;

                int index = t * phiCount + p;

                float value = values[t, p];

                // Convert selected value to radius
                float radius = EvaluateRadius(value, minValue, maxValue);

                // Spherical to Cartesian
                float sinTheta = Mathf.Sin(thetaRad);
                float x = radius * sinTheta * Mathf.Cos(phiRad);
                float y = radius * Mathf.Cos(thetaRad);
                float z = radius * sinTheta * Mathf.Sin(phiRad);

                vertices[index] = new Vector3(x, y, z);
                uvs[index] = new Vector2((float)p / (phiCount - 1), (float)t / (thetaCount - 1));

                // Normalize value to 0..1 for red intensity
                float red = Normalize01(value, minValue, maxValue);

                if (useRedGradient)
                    colors[index] = new Color(red, 0f, 0f, 1f);
                else
                    colors[index] = Color.white;
            }
        }

        // Build triangles
        int tri = 0;
        for (int t = 0; t < thetaCount - 1; t++)
        {
            for (int p = 0; p < phiCount; p++)
            {
                int pNext = (p + 1) % phiCount;

                int a = t * phiCount + p;
                int b = (t + 1) * phiCount + p;
                int c = (t + 1) * phiCount + pNext;
                int d = t * phiCount + pNext;

                triangles[tri++] = a;
                triangles[tri++] = c;
                triangles[tri++] = b;

                triangles[tri++] = a;
                triangles[tri++] = d;
                triangles[tri++] = c;
            }
        }

        // Create or reuse mesh
        if (mesh == null)
        {
            mesh = new Mesh();
            mesh.name = "PatternGainMesh";
        }
        else
        {
            mesh.Clear();
        }

        if (vertexCount > 65000)
            mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;

        mesh.vertices = vertices;
        mesh.colors = colors;
        mesh.uv = uvs;
        mesh.triangles = triangles;

        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        GetComponent<MeshFilter>().sharedMesh = mesh;
    }

    /// <summary>
    /// Returns the selected data matrix.
    /// </summary>
    float[,] GetSelectedMatrix()
    {
        switch (valueMode)
        {
            case ValueMode.Linear:
                return reconstructor.GainLinearMatrix;

            case ValueMode.RelativeDb:
                return reconstructor.GainDbRelativeMatrix;

            case ValueMode.AbsoluteDbi:
                return reconstructor.GainDbiMatrix;

            default:
                return reconstructor.GainDbiMatrix;
        }
    }

    /// <summary>
    /// Maps current value to mesh radius.
    /// </summary>
    float EvaluateRadius(float value, float minValue, float maxValue)
    {
        float n = Normalize01(value, minValue, maxValue);
        return Mathf.Max(minRadius, n * radiusScale);
    }

    /// <summary>
    /// Normalizes value to 0..1.
    /// </summary>
    float Normalize01(float value, float minValue, float maxValue)
    {
        float range = maxValue - minValue;
        if (range <= 1e-8f)
            return 0f;

        return Mathf.Clamp01((value - minValue) / range);
    }
}