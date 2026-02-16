using UnityEngine;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class OmniPatternMesh : MonoBehaviour
{
    [Header("Sampling")]
    [Range(8, 512)] public int thetaSegments = 90;   // 0..180
    [Range(8, 1024)] public int phiSegments = 180;    // 0..360

    [Header("Shape")]
    public float baseRadius = 1f;
    [Range(0.1f, 8f)] public float powerP = 1f;      // sin(theta)^p
    [Range(0f, 0.5f)] public float floor = 0f;       // prevents collapse at poles

    Mesh mesh;

    void Awake()
    {
        // Create a mesh and assign it to the MeshFilter
        mesh = new Mesh();
        mesh.name = "Omni Pattern Mesh";
        GetComponent<MeshFilter>().sharedMesh = mesh;

        BuildMesh();
    }

    void Start()
    {
        
    }

    void Update()
    {
    }

    void BuildMesh()
    {
        // Number of samples
        int vTheta = thetaSegments + 1;
        int vPhi = phiSegments + 1;

        // Arrays for vertices, colors and triangles
        Vector3[] vertices = new Vector3[vTheta * vPhi];
        Color[] colors = new Color[vTheta * vPhi];
        int[] triangles = new int[thetaSegments * phiSegments * 6]; // 2 triangles per quad, 3 indices per triangle

        // Vertices generation
        // Discretizes the continous function G(theta, phi)
        for (int t = 0; t < vTheta; t++)
        {   
            // Normalize theta
            float theta01 = t / (float)thetaSegments;
            // Convert to radians
            float theta = theta01 * Mathf.PI;

            // g(theta) = sin(theta)^p
            float g = Mathf.Pow(Mathf.Sin(theta), powerP);

            // Minimum floor to preventz zero at poles
            g = Mathf.Lerp(floor, 1f, g);

            // Convert normalized gain to radial distance
            float r = baseRadius * g;

            // Convert gain to color (white = low, red = high)
            Color c = Color.Lerp(Color.white, Color.red, g);

            for (int p = 0; p < vPhi; p++)
            {
                // Normalize phi
                float phi01 = p / (float)phiSegments;

                // Convert to radians
                float phi = phi01 * Mathf.PI * 2f;

                // Spherical coords into Cartesian
                float x = r * Mathf.Sin(theta) * Mathf.Cos(phi);
                float y = r * Mathf.Cos(theta);
                float z = r * Mathf.Sin(theta) * Mathf.Sin(phi);

                int index = t * vPhi + p;

                // Saves vertex position and color
                vertices[index] = new Vector3(x, y, z);
                colors[index] = c;
            }
        }

        // Triangles generation (2 per quad, 3 indices per triangle)
        int ti = 0;
        for (int t = 0; t < thetaSegments; t++)
        {
            for (int p = 0; p < phiSegments; p++)
            {
                // Indices of the four corners
                int i0 = t * vPhi + p;
                int i1 = i0 + 1;
                int i2 = i0 + vPhi;
                int i3 = i2 + 1;

                // First triangle
                triangles[ti++] = i0;
                triangles[ti++] = i1;
                triangles[ti++] = i2;

                // Second triangle
                triangles[ti++] = i1;
                triangles[ti++] = i3;
                triangles[ti++] = i2;
            }
        }

        // Upload to Mesh
        mesh.Clear();
        mesh.vertices = vertices;
        mesh.triangles = triangles;
        mesh.colors = colors;

        // Normals + bounds
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
    }
}
