using System;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class Vasiliadis2005PatternMeshCsv_MatlabScale : MonoBehaviour
{
    [Header("Input (.csv/.txt in StreamingAssets)")]
    public string fileName = "HWXX-6516DS1-VTM_Port 1 +45_00DT_1785.csv";

    [Header("Sampling")]
    [Range(8, 512)] public int thetaSegments = 90;    // 0..180
    [Range(8, 1024)] public int phiSegments = 180;    // 0..360

    [Header("Vasiliadis 2005")]
    [Range(0.5f, 10f)] public float k = 2f;

    [Header("MATLAB-like radius scale (dB)")]
    [Range(10f, 80f)] public float radiusRangeDb = 40f; // show from (max-range) to max
    [Range(0f, 0.5f)] public float minRadius01 = 0.05f; // prevents collapse

    [Header("Shape")]
    public float baseRadius = 2f;

    [Header("Color (absolute dBi)")]
    [Range(10f, 80f)] public float colorRangeDb = 40f;
    [Range(0.3f, 3f)] public float colorGamma = 0.8f;

    [Header("Debug")]
    public bool logAlignment = true;

    Mesh mesh;

    // Raw attenuation (dB down, 0 = max)
    float[] attH = new float[360];
    float[] attV = new float[360];

    // Aligned attenuation
    float[] attHAligned = new float[360];
    float[] attVAligned = new float[360];

    // Normalized attenuation (0 at max)
    float[] hAttNorm = new float[360];
    float[] vAttNorm = new float[360];

    // Normalized linear gain (max = 1)
    float[] hLin = new float[360];
    float[] vLin = new float[360];

    // Absolute max gain from header
    float gainMaxDbi = 0f;
    bool hasGain = false;

    void Awake()
    {
        // Create mesh
        mesh = new Mesh();
        mesh.name = "Vasiliadis 2005 (MATLAB scale)";
        GetComponent<MeshFilter>().sharedMesh = mesh;

        // Load data
        if (!LoadMsiLikeCsv())
            return;

        // Build mesh
        BuildMesh();
    }

    void OnValidate()
    {
        // Rebuild in play mode when tweaking params
        if (Application.isPlaying && mesh != null)
            BuildMesh();
    }

    // -------------------------------
    // 1) LOAD + ALIGN + NORMALIZE
    // -------------------------------
    bool LoadMsiLikeCsv()
    {
        string path = Path.Combine(Application.streamingAssetsPath, fileName);
        if (!File.Exists(path))
        {
            Debug.LogError("File not found: " + path);
            return false;
        }

        // Init
        for (int i = 0; i < 360; i++) { attH[i] = 0f; attV[i] = 0f; }

        bool readingH = false;
        bool readingV = false;

        // Parse lines
        foreach (string raw in File.ReadLines(path))
        {
            string line = raw.Trim();
            if (string.IsNullOrEmpty(line)) continue;

            // Read GAIN (robust, dBd)
            if (StartsWithToken(line, "GAIN"))
            {
                if (TryExtractFirstFloatFromLine(line, out float gDbd))
                {
                    gainMaxDbi = gDbd + 2.15f;
                    hasGain = true;
                }
                continue;
            }

            // Detect blocks
            if (StartsWithToken(line, "HORIZONTAL")) { readingH = true; readingV = false; continue; }
            if (StartsWithToken(line, "VERTICAL"))   { readingH = false; readingV = true; continue; }

            // Only numeric rows inside blocks
            if (!(readingH || readingV)) continue;

            string[] parts = line.Split(new char[] { '\t', ' ', ';', ',' }, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length < 2) continue;

            if (!TryParseFloat(parts[0], out float angleDeg)) continue;
            if (!TryParseFloat(parts[1], out float valueDb)) continue;

            int a = Mathf.RoundToInt(angleDeg) % 360;
            if (a < 0) a += 360;

            if (readingH) attH[a] = valueDb;
            else attV[a] = valueDb;
        }

        // Auto-align H: min attenuation -> phi = 0
        int hPeak = ArgMin(attH);
        int hShift = -hPeak;
        CircularShiftInto(attH, attHAligned, hShift);

        // Auto-align V: min attenuation -> theta = 90
        int vPeak = ArgMin(attV);
        int vShift = 90 - vPeak;
        CircularShiftInto(attV, attVAligned, vShift);

        if (logAlignment)
            Debug.Log($"Alignment: H peak={hPeak}° shift={hShift}, V peak={vPeak}° shift={vShift}");

        // Normalize attenuation to 0 at max
        float hMin = MinArray(attHAligned);
        float vMin = MinArray(attVAligned);

        for (int i = 0; i < 360; i++)
        {
            hAttNorm[i] = Mathf.Max(0f, attHAligned[i] - hMin);
            vAttNorm[i] = Mathf.Max(0f, attVAligned[i] - vMin);

            hLin[i] = Mathf.Pow(10f, -hAttNorm[i] / 10f);
            vLin[i] = Mathf.Pow(10f, -vAttNorm[i] / 10f);
        }

        return true;
    }

    // -------------------------------
    // 2) VASILIADIS 2005 (CROSS-WEIGHTED)
    // -------------------------------
    float GainVasiliadisLinear(float thetaRad, float phiRad)
    {
        thetaRad = Mathf.Clamp(thetaRad, 0f, Mathf.PI);
        phiRad = Mathf.Repeat(phiRad, 2f * Mathf.PI);

        // Sample normalized patterns (both are max=1)
        float h = SampleCircular360(hLin, phiRad * Mathf.Rad2Deg);

        // theta in degrees (0..180) directly samples vLin safely
        float thetaDeg = thetaRad * Mathf.Rad2Deg;
        float v = SampleCircular360(vLin, thetaDeg);

        // Cross weights
        float w1 = v * (1f - h);
        float w2 = h * (1f - v);

        // k-normalization
        float w1k = Mathf.Pow(Mathf.Max(w1, 0f), k);
        float w2k = Mathf.Pow(Mathf.Max(w2, 0f), k);
        float denom = Mathf.Pow(w1k + w2k + 1e-12f, 1f / Mathf.Max(k, 0.001f));

        float A1 = w1 / denom;
        float A2 = w2 / denom;

        // Combine in dB domain
        float GHdB = 10f * Mathf.Log10(Mathf.Max(h, 1e-12f));
        float GVdB = 10f * Mathf.Log10(Mathf.Max(v, 1e-12f));
        float Ghat_dB = GHdB * A1 + GVdB * A2;

        // Back to linear
        float g = Mathf.Pow(10f, Ghat_dB / 10f);

        if (float.IsNaN(g) || float.IsInfinity(g)) g = 0f;
        return Mathf.Clamp01(g);
    }

    // -------------------------------
    // 3) MESH (MATLAB-LIKE dB RADIUS)
    // -------------------------------
    void BuildMesh()
    {
        int vTheta = thetaSegments + 1;
        int vPhi = phiSegments; // welded seam

        Vector3[] vertices = new Vector3[vTheta * vPhi];
        Color[] colors = new Color[vTheta * vPhi];
        int[] triangles = new int[thetaSegments * phiSegments * 6];

        for (int t = 0; t < vTheta; t++)
        {
            float theta = Mathf.PI * t / thetaSegments;

            for (int p = 0; p < vPhi; p++)
            {
                float phi = 2f * Mathf.PI * p / vPhi;

                // Reconstruct normalized linear gain (0..1)
                float gLin = GainVasiliadisLinear(theta, phi);

                // Convert to relative dB (<= 0)
                float gDbRel = 10f * Mathf.Log10(Mathf.Max(gLin, 1e-12f));

                // MATLAB-like radial compression (dB scale with floor)
                float r01 = Mathf.Clamp01((gDbRel + radiusRangeDb) / Mathf.Max(1e-6f, radiusRangeDb));
                r01 = Mathf.Lerp(minRadius01, 1f, r01);
                float r = baseRadius * r01;

                // Absolute dBi for color (if GAIN exists)
                float gDbi = hasGain ? (gainMaxDbi + gDbRel) : gDbRel;

                // Color by dB-down from max
                float attDb = -gDbRel;
                float c01 = 1f - Mathf.Clamp01(attDb / Mathf.Max(1f, colorRangeDb));
                c01 = Mathf.Pow(Mathf.Clamp01(c01), colorGamma);
                Color c = Color.Lerp(Color.white, Color.red, c01);

                // Spherical -> Cartesian (phi=0 -> +Z)
                float x = r * Mathf.Sin(theta) * Mathf.Sin(phi);
                float y = r * Mathf.Cos(theta);
                float z = r * Mathf.Sin(theta) * Mathf.Cos(phi);

                int index = t * vPhi + p;
                vertices[index] = new Vector3(x, y, z);
                colors[index] = c;
            }
        }

        // Triangles with wrap
        int ti = 0;
        for (int t = 0; t < thetaSegments; t++)
        {
            for (int p = 0; p < vPhi; p++)
            {
                int p1 = (p + 1) % vPhi;

                int i0 = t * vPhi + p;
                int i1 = t * vPhi + p1;
                int i2 = (t + 1) * vPhi + p;
                int i3 = (t + 1) * vPhi + p1;

                triangles[ti++] = i0; triangles[ti++] = i2; triangles[ti++] = i1;
                triangles[ti++] = i1; triangles[ti++] = i2; triangles[ti++] = i3;
            }
        }

        mesh.Clear();
        mesh.vertices = vertices;
        mesh.triangles = triangles;
        mesh.colors = colors;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
    }

    // -------------------------------
    // 4) HELPERS
    // -------------------------------
    static float MinArray(float[] arr)
    {
        float m = float.PositiveInfinity;
        for (int i = 0; i < arr.Length; i++) m = Mathf.Min(m, arr[i]);
        return m;
    }

    static int ArgMin(float[] arr)
    {
        int idx = 0;
        float best = float.PositiveInfinity;
        for (int i = 0; i < arr.Length; i++)
        {
            if (arr[i] < best) { best = arr[i]; idx = i; }
        }
        return idx;
    }

    static void CircularShiftInto(float[] src, float[] dst, int shift)
    {
        int n = src.Length;
        for (int i = 0; i < n; i++)
        {
            int j = (i + shift) % n;
            if (j < 0) j += n;
            dst[j] = src[i];
        }
    }

    static float SampleCircular360(float[] arr360, float deg)
    {
        deg = Mathf.Repeat(deg, 360f);
        int i0 = Mathf.FloorToInt(deg) % 360;
        int i1 = (i0 + 1) % 360;
        float t = deg - Mathf.Floor(deg);
        return Mathf.Lerp(arr360[i0], arr360[i1], t);
    }

    static bool TryParseFloat(string s, out float value)
    {
        s = s.Trim().Replace(",", ".");
        return float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out value);
    }

    static bool StartsWithToken(string line, string token)
    {
        return line.StartsWith(token, StringComparison.OrdinalIgnoreCase);
    }

    static bool TryExtractFirstFloatFromLine(string line, out float value)
    {
        var m = Regex.Match(line, @"[-+]?\d+(?:[.,]\d+)?");
        if (!m.Success) { value = 0f; return false; }
        return TryParseFloat(m.Value, out value);
    }
}
