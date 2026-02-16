using System;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class Gil2001PatternMeshCsv_MatlabScale : MonoBehaviour
{
    [Header("Input (.csv/.txt in StreamingAssets)")]
    public string fileName = "HWXX-6516DS1-VTM_Port 1 +45_00DT_1785.csv";

    [Header("Sampling")]
    [Range(8, 512)] public int thetaSegments = 90;    // 0..180
    [Range(8, 1024)] public int phiSegments = 180;    // 0..360

    [Header("MATLAB-like radius scale (dB)")]
    [Range(10f, 80f)] public float radiusRangeDb = 40f; // show from (max-range) to max
    [Range(0f, 0.5f)] public float minRadius01 = 0.05f; // prevents collapse

    [Header("Shape")]
    public float baseRadius = 2f; // final radius multiplier

    [Header("Color (absolute dBi)")]
    [Range(10f, 80f)] public float colorRangeDb = 40f;  // same idea but for color ramp
    [Range(0.3f, 3f)] public float colorGamma = 0.8f;   // <1 boosts red

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

    // Vertical split for Gil (theta 0..180)
    float[] vFront = new float[181];
    float[] vBack = new float[181];

    // Absolute max gain from header
    float gainMaxDbi = 0f;
    bool hasGain = false;

    void Awake()
    {
        // Create mesh
        mesh = new Mesh();
        mesh.name = "Gil 2001 (MATLAB scale)";
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
                    gainMaxDbi = gDbd + 2.15f; // dBd -> dBi
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

        // Normalize attenuation to 0 at max (subtract min)
        float hMin = MinArray(attHAligned);
        float vMin = MinArray(attVAligned);

        for (int i = 0; i < 360; i++)
        {
            hAttNorm[i] = Mathf.Max(0f, attHAligned[i] - hMin);
            vAttNorm[i] = Mathf.Max(0f, attVAligned[i] - vMin);

            // Convert to linear power gain (normalized)
            hLin[i] = Mathf.Pow(10f, -hAttNorm[i] / 10f);
            vLin[i] = Mathf.Pow(10f, -vAttNorm[i] / 10f);
        }

        // Split vertical (front/back) for Gil
        for (int t = 0; t <= 180; t++)
        {
            vFront[t] = vLin[t];
            vBack[t] = vLin[(t + 180) % 360];
        }

        return true;
    }

    // -------------------------------
    // 2) GIL 2001 (Eq.2) IN LINEAR
    // -------------------------------
    float GainGilLinear(float thetaRad, float phiRad)
    {
        thetaRad = Mathf.Clamp(thetaRad, 0f, Mathf.PI);
        phiRad = Mathf.Repeat(phiRad, 2f * Mathf.PI);

        float Gh = SampleCircular360(hLin, phiRad * Mathf.Rad2Deg);
        float GvF = SampleClamped181(vFront, thetaRad * Mathf.Rad2Deg);
        float GvB = SampleClamped181(vBack,  thetaRad * Mathf.Rad2Deg);

        float Gnorth = vFront[0];
        float Gsouth = vFront[180];

        bool upper = thetaRad <= Mathf.PI * 0.5f;

        float theta1, theta2;
        float Gtheta1, Gtheta2;

        if (upper)
        {
            theta1 = thetaRad;
            theta2 = (Mathf.PI * 0.5f) - thetaRad;
            Gtheta1 = Gnorth;
            Gtheta2 = Gh;
        }
        else
        {
            theta1 = thetaRad - (Mathf.PI * 0.5f);
            theta2 = Mathf.PI - thetaRad;
            Gtheta1 = Gh;
            Gtheta2 = Gsouth;
        }

        float phiFold = (phiRad <= Mathf.PI) ? phiRad : (2f * Mathf.PI - phiRad);
        float phi1 = phiFold;
        float phi2 = Mathf.PI - phiFold;

        const float eps = 1e-6f;

        if (phi1 < eps) return GvF;
        if (phi2 < eps) return GvB;

        float thetaSum = theta1 + theta2;
        float phiSum = phi1 + phi2;

        float contTheta = (theta1 * theta2) / Mathf.Max(thetaSum * thetaSum, eps);
        float contPhi = (phi1 * phi2) / Mathf.Max(phiSum * phiSum, eps);

        float partPhi = (phi1 * GvB + phi2 * GvF);
        float partTheta = (theta1 * Gtheta2 + theta2 * Gtheta1);

        float num = partPhi * contTheta + partTheta * contPhi;
        float den = (phi1 + phi2) * contTheta + (theta1 + theta2) * contPhi;

        float g = num / Mathf.Max(den, eps);

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
                float gLin = GainGilLinear(theta, phi);

                // Convert to relative dB (<= 0)
                float gDbRel = 10f * Mathf.Log10(Mathf.Max(gLin, 1e-12f)); // 0 .. -inf

                // MATLAB-like radial compression (dB scale with floor)
                float r01 = Mathf.Clamp01((gDbRel + radiusRangeDb) / Mathf.Max(1e-6f, radiusRangeDb));
                r01 = Mathf.Lerp(minRadius01, 1f, r01);
                float r = baseRadius * r01;

                // Convert to absolute dBi for color (if GAIN exists)
                float gDbi = hasGain ? (gainMaxDbi + gDbRel) : gDbRel;

                // Color by dB-down from max (similar to MATLAB colorbar range)
                float attDb = -gDbRel; // 0..+
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

    static float SampleClamped181(float[] arr181, float deg)
    {
        deg = Mathf.Clamp(deg, 0f, 180f);
        int i0 = Mathf.FloorToInt(deg);
        int i1 = Mathf.Min(i0 + 1, 180);
        float t = deg - i0;
        return Mathf.Lerp(arr181[i0], arr181[i1], t);
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
