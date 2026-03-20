using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

/// <summary>
/// Singleton that reads an input CSV from StreamingAssets, reconstructs a 3D gain matrix,
/// and keeps the result available for other scripts.
/// 
/// Matrix:
///   [theta, phi]
///   theta = 0..180
///   phi   = 0..359
/// </summary>
[DefaultExecutionOrder(-1000)] // Runs the first
public class PatternGainReconstructor : MonoBehaviour
{
    // --------------------------------------------------
    // Input parameters
    // --------------------------------------------------

    [Header("Input file name")]
    public string fileName = "HWXX-6516DS1-VTM_Port 1 +45_00DT_1785.csv";

    [Header("Method")]
    public ReconstructionMethod method = ReconstructionMethod.Vasiliadis2005;

    [Header("Vasiliadis 2005")]
    [Range(0.5f, 10f)] public float k = 2f;

    [Header("Omni")]
    [Range(0.1f, 8f)] public float omniPowerP = 1f;
    [Range(0f, 0.5f)] public float omniFloor = 0f;


    [Header("Debug")]
    public bool logAlignment = true;
    public bool verboseLogs = true;

    // --------------------------------------------------
    // Internal state
    // --------------------------------------------------


    // Singleton instance
    public static PatternGainReconstructor Instance { get; private set; }

    // Reconstructon methods
    public enum ReconstructionMethod
    {
        Gil2001,
        Vasiliadis2005,
        Omni
    }

    // Ready flag
    public bool IsReady { get; private set; }

    // Output matrices
    public float[,] GainLinearMatrix { get; private set; }      // normalized linear gain
    public float[,] GainDbRelativeMatrix { get; private set; }  // relative dB (0 at max)
    public float[,] GainDbiMatrix { get; private set; }         // absolute dBi if GAIN exists

    // Metadata
    public bool HasAbsoluteGain => hasGain;
    public float MaxGainDbi => gainMaxDbi;

    // Raw input slices
    readonly float[] attH = new float[360];
    readonly float[] attV = new float[360];

    // Aligned slices
    readonly float[] attHAligned = new float[360];
    readonly float[] attVAligned = new float[360];

    // Normalized linear slices
    readonly float[] hLin = new float[360];
    readonly float[] vLin = new float[360];

    // Vertical split for Gil
    readonly float[] vFront = new float[181];
    readonly float[] vBack = new float[181];

    // Absolute gain from header
    float gainMaxDbi = 0f;
    bool hasGain = false;

    void Awake()
    {
        // Singleton pattern
        if (Instance != null && Instance != this)
        {
            Debug.LogWarning($"Duplicate {nameof(PatternGainReconstructor)} on {name}. Destroying duplicate.");
            Destroy(this);
            return;
        }

        Instance = this;

        Compute();
    }

    /// <summary>
    /// Computes the full matrix.
    /// </summary>
    private void Compute()
    {
        IsReady = false;

        if (method == ReconstructionMethod.Omni)
        {
            BuildOmniMatrices();
        }
        else
        {
            if (!LoadMsiLikeCsv())
                return;

            BuildGainMatrices();
        }

        IsReady = true;

        if (verboseLogs)
            Debug.Log($"[{nameof(PatternGainReconstructor)}] Matrix ready. Method={method}, size=181x360, absoluteDbi={(hasGain ? "yes" : "no")}");
    }

    // --------------------------------------------------
    // Getters
    // ---------------------------------------------------

    /// <summary>
    /// Gets normalized linear gain.
    /// </summary>
    public float GetGainLinear(int thetaDeg, int phiDeg)
    {
        EnsureReady();
        return GainLinearMatrix[ClampTheta(thetaDeg), Wrap360(phiDeg)];
    }

    /// <summary>
    /// Gets relative dB gain.
    /// 0 dB = maximum.
    /// </summary>
    public float GetGainDbRelative(int thetaDeg, int phiDeg)
    {
        EnsureReady();
        return GainDbRelativeMatrix[ClampTheta(thetaDeg), Wrap360(phiDeg)];
    }

    /// <summary>
    /// Gets absolute dBi gain if available.
    /// </summary>
    public float GetGainDbi(int thetaDeg, int phiDeg)
    {
        EnsureReady();
        return GainDbiMatrix[ClampTheta(thetaDeg), Wrap360(phiDeg)];
    }

    /// <summary>
    /// Gets normalized linear gain with bilinear interpolation.
    /// </summary>
    public float GetGainLinear(float thetaDeg, float phiDeg)
    {
        EnsureReady();
        return SampleBilinearThetaPhi(GainLinearMatrix, thetaDeg, phiDeg);
    }

    /// <summary>
    /// Gets relative dB gain with bilinear interpolation.
    /// </summary>
    public float GetGainDbRelative(float thetaDeg, float phiDeg)
    {
        EnsureReady();
        return SampleBilinearThetaPhi(GainDbRelativeMatrix, thetaDeg, phiDeg);
    }

    /// <summary>
    /// Gets absolute dBi gain with bilinear interpolation.
    /// </summary>
    public float GetGainDbi(float thetaDeg, float phiDeg)
    {
        EnsureReady();
        return SampleBilinearThetaPhi(GainDbiMatrix, thetaDeg, phiDeg);
    }


    // --------------------------------------------------
    // Prepare data from CSV
    // --------------------------------------------------
    private bool LoadMsiLikeCsv()
    {
        string path = Path.Combine(Application.streamingAssetsPath, fileName);

        // If the file doesn't exist, logs an error and return false
        if (!File.Exists(path))
        {
            Debug.LogError("File not found: " + path);
            return false;
        }

        // Reset arrays
        Array.Clear(attH, 0, attH.Length);
        Array.Clear(attV, 0, attV.Length);
        Array.Clear(attHAligned, 0, attHAligned.Length);
        Array.Clear(attVAligned, 0, attVAligned.Length);
        Array.Clear(hLin, 0, hLin.Length);
        Array.Clear(vLin, 0, vLin.Length);
        Array.Clear(vFront, 0, vFront.Length);
        Array.Clear(vBack, 0, vBack.Length);

        gainMaxDbi = 0f;
        hasGain = false;

        bool readingH = false;
        bool readingV = false;

        // Parse file line by line
        foreach (string raw in File.ReadLines(path))
        {
            string line = raw.Trim();
            if (string.IsNullOrEmpty(line))
                continue;

            // Read GAIN from header
            if (StartsWithToken(line, "GAIN"))
            {
                if (TryExtractFirstFloatFromLine(line, out float gDbd))
                {
                    // Converts from dBd to dBi
                    gainMaxDbi = gDbd + 2.15f; // dBd -> dBi
                    hasGain = true;
                }
                continue;
            }

            // Detect slice blocks
            if (StartsWithToken(line, "HORIZONTAL"))
            {
                readingH = true;
                readingV = false;
                continue;
            }

            if (StartsWithToken(line, "VERTICAL"))
            {
                readingH = false;
                readingV = true;
                continue;
            }

            // Ignore non-slice lines
            if (!(readingH || readingV))
                continue;

            // Read numeric rows
            string[] parts = line.Split(new[] { '\t', ' ', ';', ',' }, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length < 2)
                continue;

            if (!TryParseFloat(parts[0], out float angleDeg))
                continue;
            if (!TryParseFloat(parts[1], out float valueDb))
                continue;

            // If 
            int a = Wrap360(Mathf.RoundToInt(angleDeg));

            if (readingH)
            {
                attH[a] = valueDb;
            }
            else
            {
                attV[a] = valueDb;
            }
        }

        // Align H peak to phi = 0
        int hPeak = ArgMin(attH);
        int hShift = -hPeak;
        CircularShiftInto(attH, attHAligned, hShift);

        // Align V peak to theta = 90
        int vPeak = ArgMin(attV);
        int vShift = 90 - vPeak;
        CircularShiftInto(attV, attVAligned, vShift);

        if (logAlignment)
            Debug.Log($"Alignment: H peak={hPeak}° shift={hShift}, V peak={vPeak}° shift={vShift}");

        // Convert aligned attenuation to normalized linear gain
        float hMin = MinArray(attHAligned);
        float vMin = MinArray(attVAligned);

        for (int i = 0; i < 360; i++)
        {
            float hAtt = Mathf.Max(0f, attHAligned[i] - hMin);
            float vAtt = Mathf.Max(0f, attVAligned[i] - vMin);

            hLin[i] = Mathf.Pow(10f, -hAtt / 10f);
            vLin[i] = Mathf.Pow(10f, -vAtt / 10f);
        }

        // Split vertical cut for Gil
        for (int t = 0; t <= 180; t++)
        {
            vFront[t] = vLin[t];
            vBack[t] = vLin[(t + 180) % 360];
        }

        return true;
    }

    // --------------------------------------------------
    // 2) BUILD OUTPUT MATRICES
    // --------------------------------------------------
    void BuildGainMatrices()
    {
        GainLinearMatrix = new float[181, 360];
        GainDbRelativeMatrix = new float[181, 360];
        GainDbiMatrix = new float[181, 360];

        for (int theta = 0; theta <= 180; theta++)
        {
            for (int phi = 0; phi < 360; phi++)
            {
                float gLin = EvaluateDirection(theta, phi);

                // Relative dB
                float gDbRel = 10f * Mathf.Log10(Mathf.Max(gLin, 1e-12f));

                // Absolute dBi
                float gDbi = hasGain ? gainMaxDbi + gDbRel : gDbRel;

                GainLinearMatrix[theta, phi] = gLin;
                GainDbRelativeMatrix[theta, phi] = gDbRel;
                GainDbiMatrix[theta, phi] = gDbi;
            }
        }
    }

    void BuildOmniMatrices()
    {
        GainLinearMatrix = new float[181, 360];
        GainDbRelativeMatrix = new float[181, 360];
        GainDbiMatrix = new float[181, 360];

        hasGain = false;
        gainMaxDbi = 0f;

        for (int theta = 0; theta <= 180; theta++)
        {
            float thetaRad = theta * Mathf.Deg2Rad;
            float gLin = Mathf.Pow(Mathf.Sin(thetaRad), omniPowerP);
            gLin = Mathf.Lerp(omniFloor, 1f, gLin);

            float gDbRel = 10f * Mathf.Log10(Mathf.Max(gLin, 1e-12f));

            for (int phi = 0; phi < 360; phi++)
            {
                GainLinearMatrix[theta, phi] = gLin;
                GainDbRelativeMatrix[theta, phi] = gDbRel;
                GainDbiMatrix[theta, phi] = gDbRel;
            }
        }
    }

    // --------------------------------------------------
    // 3) RECONSTRUCTION DISPATCH
    // --------------------------------------------------
    float EvaluateDirection(float thetaDeg, float phiDeg)
    {
        switch (method)
        {
            case ReconstructionMethod.Gil2001:
                return GainGilLinear(thetaDeg, phiDeg);

            case ReconstructionMethod.Vasiliadis2005:
                return GainVasiliadisLinear(thetaDeg, phiDeg);

            case ReconstructionMethod.Omni:
            {
                float thetaRad = thetaDeg * Mathf.Deg2Rad;
                float g = Mathf.Pow(Mathf.Sin(thetaRad), omniPowerP);
                return Mathf.Lerp(omniFloor, 1f, g);
            }

            default:
                return 0f;
        }
    }

    // --------------------------------------------------
    // 4) GIL 2001
    // --------------------------------------------------
    float GainGilLinear(float thetaDeg, float phiDeg)
    {
        float thetaRad = Mathf.Clamp(thetaDeg, 0f, 180f) * Mathf.Deg2Rad;
        float phiRad = Mathf.Repeat(phiDeg, 360f) * Mathf.Deg2Rad;

        float Gh = SampleCircular360(hLin, phiDeg);
        float GvF = SampleClamped181(vFront, thetaDeg);
        float GvB = SampleClamped181(vBack, thetaDeg);

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

        if (float.IsNaN(g) || float.IsInfinity(g))
            g = 0f;

        return Mathf.Clamp01(g);
    }

    // --------------------------------------------------
    // 5) VASILIADIS 2005
    // --------------------------------------------------
    float GainVasiliadisLinear(float thetaDeg, float phiDeg)
    {
        float h = SampleCircular360(hLin, phiDeg);
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
        float GhatDb = GHdB * A1 + GVdB * A2;

        // Back to linear
        float g = Mathf.Pow(10f, GhatDb / 10f);

        if (float.IsNaN(g) || float.IsInfinity(g))
            g = 0f;

        return Mathf.Clamp01(g);
    }

    // --------------------------------------------------
    // 7) HELPERS
    // --------------------------------------------------
    static float SampleBilinearThetaPhi(float[,] matrix, float thetaDeg, float phiDeg)
    {
        thetaDeg = Mathf.Clamp(thetaDeg, 0f, 180f);
        phiDeg = Mathf.Repeat(phiDeg, 360f);

        int t0 = Mathf.FloorToInt(thetaDeg);
        int t1 = Mathf.Min(t0 + 1, 180);

        int p0 = Mathf.FloorToInt(phiDeg) % 360;
        int p1 = (p0 + 1) % 360;

        float ft = thetaDeg - t0;
        float fp = phiDeg - Mathf.Floor(phiDeg);

        float a = Mathf.Lerp(matrix[t0, p0], matrix[t0, p1], fp);
        float b = Mathf.Lerp(matrix[t1, p0], matrix[t1, p1], fp);

        return Mathf.Lerp(a, b, ft);
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

    static float MinArray(float[] arr)
    {
        float m = float.PositiveInfinity;
        for (int i = 0; i < arr.Length; i++)
            m = Mathf.Min(m, arr[i]);
        return m;
    }

    static int ArgMin(float[] arr)
    {
        int idx = 0;
        float best = float.PositiveInfinity;

        for (int i = 0; i < arr.Length; i++)
        {
            if (arr[i] < best)
            {
                best = arr[i];
                idx = i;
            }
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

    static int Wrap360(int deg)
    {
        deg %= 360;
        if (deg < 0) deg += 360;
        return deg;
    }

    static int ClampTheta(int deg)
    {
        return Mathf.Clamp(deg, 0, 180);
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
        Match m = Regex.Match(line, @"[-+]?\d+(?:[.,]\d+)?");
        if (!m.Success)
        {
            value = 0f;
            return false;
        }

        return TryParseFloat(m.Value, out value);
    }

    void EnsureReady()
    {
        if (!IsReady || GainLinearMatrix == null || GainDbRelativeMatrix == null || GainDbiMatrix == null)
            throw new InvalidOperationException($"{nameof(PatternGainReconstructor)} is not ready yet.");
    }
}