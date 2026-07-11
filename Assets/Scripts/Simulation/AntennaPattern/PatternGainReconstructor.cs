using System;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;

/// <summary>
/// Singleton that reads an input CSV from StreamingAssets.
/// It reconstructs a 3D gain matrix and keeps the result available for other scripts.
/// 
/// Matrix.
///   [theta, phi].
///   theta = 0 to 180.
///   phi   = 0 to 359.
/// </summary>
[DefaultExecutionOrder(-1000)] // Runs the first
public class PatternGainReconstructor : MonoBehaviour
{
    // Reconstruction methods
    public enum ReconstructionMethod
    {
        Gil2001,
        Vasiliadis2005,
        Omni
    }

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
    [Range(0.1f, 8f)] public float omniPowerP = 2f;
    [Range(0f, 0.5f)] public float omniFloor = 0f;
    public float omniMaxGainDbi = 0f;

    // Singleton instance
    public static PatternGainReconstructor Instance { get; private set; }

    // Ready flag
    public bool IsReady { get; private set; }

    // Output matrices
    public float[,] GainLinearMatrix { get; private set; }      // normalized linear gain
    public float[,] GainDbRelativeMatrix { get; private set; }  // relative dB (0 at max)
    public float[,] GainDbiMatrix { get; private set; }         // absolute dBi if GAIN exists

    // Info about absolute gain from header
    public bool HasAbsoluteGain => hasGain;
    public float MaxGainDbi => gainMaxDbi;

    // Original slices
    private float[] attH = new float[360];
    private float[] attV = new float[360];

    // Aligned attenuation slices
    private float[] attHAligned = new float[360];
    private float[] attVAligned = new float[360];

    // Normalized linear slices
    private float[] hLin = new float[360];
    private float[] vLin = new float[360];

    // Vertical split for Gil
    private float[] vFront = new float[181];
    private float[] vBack = new float[181];

    // Absolute gain from header
    private float gainMaxDbi = 0f;
    private bool hasGain = false;

    /// <summary>
    /// Initializes the singleton instance and computes the first gain matrix.
    /// </summary>
    void Awake()
    {
        // Singleton pattern
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;

        Compute();
    }

    /// <summary>
    /// Recomputes the gain matrix when Inspector values change during play mode.
    /// </summary>
    void OnValidate()
    {
        if (!Application.isPlaying)
        {
            return;
        }

        Compute();
    }

    /// <summary>
    /// Computes the full matrix.
    /// </summary>
    private void Compute()
    {
        // Resets output matrices
        GainLinearMatrix = null;
        GainDbRelativeMatrix = null;
        GainDbiMatrix = null;

        IsReady = false;

        if (method == ReconstructionMethod.Omni)
        {
            BuildOmniMatrices();
        }
        else
        {
            if (!LoadMsiLikeCsv())
            {
                return;
            }
            BuildGainMatrices();
        }

        IsReady = true;
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
    /// 16 dB = maximum.
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
    /// Exports the reconstructed absolute gain matrix to a tab separated CSV file.
    /// </summary>
    public void ExportGainDbiMatrixCsv(string outputPath)
    {
        EnsureReady();

        using (StreamWriter writer = new StreamWriter(outputPath))
        {
            // Writes metadata using the same header style as the input pattern file
            writer.WriteLine("FILENAME\t" + fileName);
            writer.WriteLine("METHOD\t" + method);

            if (method == ReconstructionMethod.Vasiliadis2005)
            {
                writer.WriteLine("K_FACTOR\t" + k.ToString("F2", CultureInfo.InvariantCulture));
            }

            if (method == ReconstructionMethod.Omni)
            {
                writer.WriteLine("OMNI_MAX_GAIN_DBI\t" + omniMaxGainDbi.ToString("F6", CultureInfo.InvariantCulture));
                writer.WriteLine("OMNI_POWER_P\t" + omniPowerP.ToString("F6", CultureInfo.InvariantCulture));
                writer.WriteLine("OMNI_FLOOR\t" + omniFloor.ToString("F6", CultureInfo.InvariantCulture));
            }

            writer.WriteLine("THETA_COUNT\t" + GainDbiMatrix.GetLength(0));
            writer.WriteLine("PHI_COUNT\t" + GainDbiMatrix.GetLength(1));
            writer.WriteLine("UNITS\tdBi");
            writer.WriteLine("THETA\tPHI\tGAIN");

            // Writes one row per reconstructed direction
            for (int theta = 0; theta < GainDbiMatrix.GetLength(0); theta++)
            {
                for (int phi = 0; phi < GainDbiMatrix.GetLength(1); phi++)
                {
                    writer.WriteLine(
                        theta.ToString("F2", CultureInfo.InvariantCulture) + "\t" +
                        phi.ToString("F2", CultureInfo.InvariantCulture) + "\t" +
                        GainDbiMatrix[theta, phi].ToString("F6", CultureInfo.InvariantCulture)
                    );
                }
            }
        }
    }

    // --------------------------------------------------
    // Prepare data from CSV
    // --------------------------------------------------
    /// <summary>
    /// Loads horizontal and vertical slices from the MSI like CSV file.
    /// </summary>
    private bool LoadMsiLikeCsv()
    {
        string path = Path.Combine(Application.streamingAssetsPath, fileName);

        // If the file doesn't exist, returns false
        if (!File.Exists(path))
        {
            Debug.LogError($"File not found: {path}");
            return false;
        }

        // Resets arrays
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

        // Parses file line by line
        foreach (string raw in File.ReadLines(path))
        {
            string line = raw.Trim();
            if (string.IsNullOrEmpty(line))
            {
                continue;
            }

            // Reads GAIN from header
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

            // Detects horizontal slice start
            if (StartsWithToken(line, "HORIZONTAL"))
            {
                readingH = true;
                readingV = false;
                continue;
            }

            // Detects vertical slice start
            if (StartsWithToken(line, "VERTICAL"))
            {
                readingH = false;
                readingV = true;
                continue;
            }

            // Ignores invalid lines
            if (!(readingH || readingV))
            {
                continue;
            }

            // Reads numeric rows
            string[] parts = line.Split(new[] { '\t', ' ', ';', ',' }, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length < 2)
            {
                continue;
            }


            if (!TryParseFloat(parts[0], out float angleDeg))
            {
                continue;
            }

            if (!TryParseFloat(parts[1], out float valueDb))
            {
                continue;
            }


            // Maps angle to the 0 to 359 index range
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

        // Keep H cut in the original CSV azimuth convention
        Array.Copy(attH, attHAligned, attH.Length);

        // Match theta = original vertical angle + 90
        int vShift = 90;
        CircularShiftInto(attV, attVAligned, vShift);

        // Converts aligned attenuation to normalized linear gain
        float hMin = MinArray(attHAligned);
        float vMin = MinArray(attVAligned);


        // Converts from dB attenuation to linear gain
        for (int i = 0; i < 360; i++)
        {
            float hAtt = Mathf.Max(0f, attHAligned[i] - hMin);
            float vAtt = Mathf.Max(0f, attVAligned[i] - vMin);

            hLin[i] = Mathf.Pow(10f, -hAtt / 10f);
            vLin[i] = Mathf.Pow(10f, -vAtt / 10f);
        }

        // Step 1 for Gil, used here not to it each time we evaluate a direction
        for (int t = 0; t <= 180; t++)
        {
            vFront[t] = vLin[t];
            vBack[t] = vLin[(t + 180) % 360];
        }
        return true;
    }

    // --------------------------------------------------
    // Build matrices
    // --------------------------------------------------
    /// <summary>
    /// Builds the linear, relative dB and absolute dBi gain matrices.
    /// </summary>
    private void BuildGainMatrices()
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
                float gDbi;
                if (hasGain)
                {
                    gDbi = gainMaxDbi + gDbRel;
                }
                else
                {
                    gDbi = gDbRel;
                }

                // Save value in matrices
                GainLinearMatrix[theta, phi] = gLin;
                GainDbRelativeMatrix[theta, phi] = gDbRel;
                GainDbiMatrix[theta, phi] = gDbi;
            }
        }
    }

    /// <summary>
    /// Builds a simple omnidirectional gain matrix.
    /// </summary>
    private void BuildOmniMatrices()
    {
        GainLinearMatrix = new float[181, 360];
        GainDbRelativeMatrix = new float[181, 360];
        GainDbiMatrix = new float[181, 360];

        hasGain = false;
        gainMaxDbi = 0f;

        for (int theta = 0; theta <= 180; theta++)
        {
            // Converts theta to radians
            float thetaRad = theta * Mathf.Deg2Rad;

            // Gets gain from sine power pattern
            float gLin = Mathf.Pow(Mathf.Sin(thetaRad), omniPowerP);

            // Applies floor
            gLin = Mathf.Lerp(omniFloor, 1f, gLin);

            // Gets relative dB from linear gain
            float gDbRel = 10f * Mathf.Log10(Mathf.Max(gLin, 1e-12f));

            for (int phi = 0; phi < 360; phi++)
            {
                GainLinearMatrix[theta, phi] = gLin;
                GainDbRelativeMatrix[theta, phi] = gDbRel;
                // Adds the configured maximum gain to convert relative dB into dBi
                GainDbiMatrix[theta, phi] = omniMaxGainDbi + gDbRel;
            }
        }
    }

    // --------------------------------------------------
    // Reconstruction methods
    // --------------------------------------------------
    /// <summary>
    /// Selects the active reconstruction method for one direction.
    /// </summary>
    private float EvaluateDirection(int thetaDeg, int phiDeg)
    {
        switch (method)
        {
            case ReconstructionMethod.Gil2001:
                return CalculateGainByGil(thetaDeg, phiDeg);
            case ReconstructionMethod.Vasiliadis2005:
                return CalculateGainByVasiliadis(thetaDeg, phiDeg);
            default:
                return 0f;
        }
    }

    // --------------------------------------------------
    // GIL 2001
    // --------------------------------------------------
    /// <summary>
    /// Calculates one direction using the Gil reconstruction method.
    /// </summary>
    private float CalculateGainByGil(int thetaDeg, int phiDeg)
    {

        // Converts angles to radians
        float thetaRad = thetaDeg * Mathf.Deg2Rad;
        float phiRad = phiDeg * Mathf.Deg2Rad;


        // 1 - Done in LoadMsiLikeCsv to avoid doing it each time we evaluate a direction

        // 2 - Samples used values for a given direction

        // Horizontal (Equator)
        float Gh = hLin[Wrap360(phiDeg)];

        // Vertical front
        float GvF = vFront[ClampTheta(thetaDeg)];

        // Vertical back
        float GvB = vBack[ClampTheta(thetaDeg)];

        // Poles
        float Gnorth = vFront[0];
        float Gsouth = vFront[180];

        // 3 - Choose hemisphere
        bool upper = thetaRad <= Mathf.PI / 2f;

        float theta1, theta2;
        float Gtheta1, Gtheta2;

        // 4 - Define distances in theta and limit values

        // For upper hemisphere
        if (upper)
        {
            theta1 = thetaRad;
            theta2 = (Mathf.PI / 2f) - thetaRad;
            Gtheta1 = Gnorth;
            Gtheta2 = Gh;
        }
        else // For lower hemisphere
        {
            theta1 = thetaRad - (Mathf.PI / 2f);
            theta2 = Mathf.PI - thetaRad;
            Gtheta1 = Gh;
            Gtheta2 = Gsouth;
        }

        // 5 - Define distances between phi and meridians
        float phiFold; // min(phi, 2pi - phi)
        if (phiRad <= Mathf.PI)
        {
            phiFold = phiRad;
        }
        else
        {
            phiFold = 2f * Mathf.PI - phiRad;
        }

        float phi1 = phiFold; // Distance to phi = 0
        float phi2 = Mathf.PI - phiFold; // Distance to phi = pi

        // 6 - Final formula

        // Epsilon to avoid division by zero
        const float eps = 1e-6f;

        // If phi is very close to 0 or 180, we can directly return the corresponding meridian gain
        if (phi1 < eps)
        {
            return GvF;
        }

        if (phi2 < eps)
        {
            return GvB;
        }

        // Continuity factors
        float contTheta = (theta1 * theta2) / Mathf.Max((theta1 + theta2) * (theta1 + theta2), eps);
        float contPhi = (phi1 * phi2) / Mathf.Max((phi1 + phi2) * (phi1 + phi2), eps);

        // Main parts
        float partPhi = (phi1 * GvB + phi2 * GvF);
        float partTheta = (theta1 * Gtheta2 + theta2 * Gtheta1);

        // Final gain
        float num = partPhi * contTheta + partTheta * contPhi;
        float den = (phi1 + phi2) * contTheta + (theta1 + theta2) * contPhi;

        // Avoids division by zero
        float g = num / Mathf.Max(den, eps);

        // Clamps to [0, 1] and handles NaN/Infinity
        if (float.IsNaN(g) || float.IsInfinity(g))
        {
            g = 0f;
        }

        return Mathf.Clamp01(g);
    }

    // --------------------------------------------------
    // VASILIADIS 2005
    // --------------------------------------------------
    /// <summary>
    /// Calculates one direction using the Vasiliadis reconstruction method.
    /// </summary>
    private float CalculateGainByVasiliadis(int thetaDeg, int phiDeg)
    {
        // 1 - Sample normalized values
        float h = hLin[Wrap360(phiDeg)];
        float v = vLin[ClampTheta(thetaDeg)];

        // 2 - Cross weights
        float w1 = v * (1f - h);
        float w2 = h * (1f - v);

        // 3 - k-normalization
        float w1k = Mathf.Pow(Mathf.Max(w1, 0f), k);
        float w2k = Mathf.Pow(Mathf.Max(w2, 0f), k);
        float den = Mathf.Pow(w1k + w2k + 1e-12f, 1f / Mathf.Max(k, 0.001f));

        float A1 = w1 / den;
        float A2 = w2 / den;

        // 4 - Combine in dB and back to linear

        // Combine
        float GH = 10f * Mathf.Log10(Mathf.Max(h, 1e-12f));
        float GV = 10f * Mathf.Log10(Mathf.Max(v, 1e-12f));
        float GDb = GH * A1 + GV * A2;

        // Back to linear
        float g = Mathf.Pow(10f, GDb / 10f);

        if (float.IsNaN(g) || float.IsInfinity(g))
        {
            g = 0f;
        }

        return Mathf.Clamp01(g);
    }

    // --------------------------------------------------
    // HELPERS
    // --------------------------------------------------

    /// <summary>
    /// Returns the smallest value in an array.
    /// </summary>
    private static float MinArray(float[] arr)
    {
        // Starts with a very large value
        float m = float.PositiveInfinity;

        // Checks all elements
        for (int i = 0; i < arr.Length; i++)
            m = Mathf.Min(m, arr[i]);

        return m;
    }

    /// <summary>
    /// Returns the index of the smallest value in an array.
    /// </summary>
    private static int ArgMin(float[] arr)
    {
        // Starts assuming the first valid minimum
        int idx = 0;
        float best = float.PositiveInfinity;

        // Searches for the smallest value
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

    /// <summary>
    /// Copies an array into another one with a circular shift.
    /// </summary>
    private static void CircularShiftInto(float[] src, float[] dst, int shift)
    {
        int n = src.Length;

        for (int i = 0; i < n; i++)
        {
            // Computes shifted position
            int j = (i + shift) % n;

            // Fixes negative positions
            if (j < 0) j += n;

            dst[j] = src[i];
        }
    }

    /// <summary>
    /// Wraps an angle to the 0 to 359 range.
    /// </summary>
    private static int Wrap360(int deg)
    {
        deg = deg % 360;

        if (deg < 0)
        {
            deg += 360;
        }


        return deg;
    }

    /// <summary>
    /// Clamps theta to the valid 0 to 180 range.
    /// </summary>
    private static int ClampTheta(int deg)
    {
        return Mathf.Clamp(deg, 0, 180);
    }

    /// <summary>
    /// Tries to parse a float using invariant culture.
    /// </summary>
    private static bool TryParseFloat(string s, out float value)
    {
        // Removes spaces and replaces comma with dot
        s = s.Trim().Replace(",", ".");

        return float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out value);
    }

    /// <summary>
    /// Checks whether a line starts with a token.
    /// </summary>
    private static bool StartsWithToken(string line, string token)
    {
        return line.StartsWith(token, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Extracts the first float found inside a line.
    /// </summary>
    private static bool TryExtractFirstFloatFromLine(string line, out float value)
    {
        Match m = Regex.Match(line, @"[-+]?\d+(?:[.,]\d+)?");

        if (!m.Success)
        {
            value = 0f;
            return false;
        }

        return TryParseFloat(m.Value, out value);
    }

    /// <summary>
    /// Throws an exception if the reconstructed matrices are not ready.
    /// </summary>
    private void EnsureReady()
    {
        if (!IsReady || GainLinearMatrix == null || GainDbRelativeMatrix == null || GainDbiMatrix == null)
        {
            throw new InvalidOperationException($"{nameof(PatternGainReconstructor)} is not ready yet.");
        }

    }
}
