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
    /// <summary>
    /// Available methods for generating the antenna gain matrix.
    /// </summary>
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

    [Header("Debug")]
    public bool logCutSamples = false;

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
    private float[] horizontalAttenuation = new float[360];
    private float[] verticalAttenuation = new float[360];

    // Aligned attenuation slices
    private float[] alignedHorizontalAttenuation = new float[360];
    private float[] alignedVerticalAttenuation = new float[360];

    // Normalized linear slices
    private float[] horizontalLinearGain = new float[360];
    private float[] verticalLinearGain = new float[360];

    // Vertical split for Gil
    private float[] frontVerticalLinearGain = new float[181];
    private float[] backVerticalLinearGain = new float[181];

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

        if (logCutSamples)
        {
            LogCutSamples();
        }
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
    /// Prints sample gain values used to compare reconstructed cuts with the original CSV slices.
    /// </summary>
    private void LogCutSamples()
    {
        if (method == ReconstructionMethod.Omni)
        {
            return;
        }

        LogCutSample(90, 25);
        LogCutSample(90, 68);
        LogCutSample(90, 180);
        LogCutSample(135, 0);
    }

    /// <summary>
    /// Prints one reconstructed gain sample for a theta and phi pair.
    /// </summary>
    private void LogCutSample(int theta, int phi)
    {
        float relativeDb = GetGainDbRelative(theta, phi);
        float absoluteDbi = GetGainDbi(theta, phi);

        Debug.Log(
            $"Pattern sample (theta={theta} phi={phi}) " +
            $"relative={relativeDb:F2} dB absolute={absoluteDbi:F2} dBi"
        );
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
        Array.Clear(horizontalAttenuation, 0, horizontalAttenuation.Length);
        Array.Clear(verticalAttenuation, 0, verticalAttenuation.Length);
        Array.Clear(alignedHorizontalAttenuation, 0, alignedHorizontalAttenuation.Length);
        Array.Clear(alignedVerticalAttenuation, 0, alignedVerticalAttenuation.Length);
        Array.Clear(horizontalLinearGain, 0, horizontalLinearGain.Length);
        Array.Clear(verticalLinearGain, 0, verticalLinearGain.Length);
        Array.Clear(frontVerticalLinearGain, 0, frontVerticalLinearGain.Length);
        Array.Clear(backVerticalLinearGain, 0, backVerticalLinearGain.Length);

        gainMaxDbi = 0f;
        hasGain = false;

        bool readingHorizontalSlice = false;
        bool readingVerticalSlice = false;

        // Parses file line by line
        foreach (string rawLine in File.ReadLines(path))
        {
            string line = rawLine.Trim();
            if (string.IsNullOrEmpty(line))
            {
                continue;
            }

            // Reads GAIN from header
            if (StartsWithToken(line, "GAIN"))
            {
                if (TryExtractFirstFloatFromLine(line, out float gainDbd))
                {
                    // Converts from dBd to dBi
                    gainMaxDbi = gainDbd + 2.15f; // dBd -> dBi
                    hasGain = true;
                }
                continue;
            }

            // Detects horizontal slice start
            if (StartsWithToken(line, "HORIZONTAL"))
            {
                readingHorizontalSlice = true;
                readingVerticalSlice = false;
                continue;
            }

            // Detects vertical slice start
            if (StartsWithToken(line, "VERTICAL"))
            {
                readingHorizontalSlice = false;
                readingVerticalSlice = true;
                continue;
            }

            // Ignores invalid lines
            if (!(readingHorizontalSlice || readingVerticalSlice))
            {
                continue;
            }

            // Reads numeric rows
            string[] lineParts = line.Split(new[] { '\t', ' ', ';', ',' }, StringSplitOptions.RemoveEmptyEntries);
            if (lineParts.Length < 2)
            {
                continue;
            }


            if (!TryParseFloat(lineParts[0], out float angleDegrees))
            {
                continue;
            }

            if (!TryParseFloat(lineParts[1], out float valueDb))
            {
                continue;
            }


            // Maps angle to the 0 to 359 index range
            int angleIndex = Wrap360(Mathf.RoundToInt(angleDegrees));

            if (readingHorizontalSlice)
            {
                horizontalAttenuation[angleIndex] = valueDb;
            }
            else
            {
                verticalAttenuation[angleIndex] = valueDb;
            }
        }

        // Keep H cut in the original CSV azimuth convention
        Array.Copy(horizontalAttenuation, alignedHorizontalAttenuation, horizontalAttenuation.Length);

        // Match theta = original vertical angle + 90
        int verticalShift = 90;
        CircularShiftInto(verticalAttenuation, alignedVerticalAttenuation, verticalShift);

        // Converts aligned attenuation to normalized linear gain
        float horizontalMinimumAttenuation = MinArray(alignedHorizontalAttenuation);
        float verticalMinimumAttenuation = MinArray(alignedVerticalAttenuation);


        // Converts from dB attenuation to linear gain
        for (int i = 0; i < 360; i++)
        {
            float horizontalRelativeAttenuation = Mathf.Max(0f, alignedHorizontalAttenuation[i] - horizontalMinimumAttenuation);
            float verticalRelativeAttenuation = Mathf.Max(0f, alignedVerticalAttenuation[i] - verticalMinimumAttenuation);

            horizontalLinearGain[i] = Mathf.Pow(10f, -horizontalRelativeAttenuation / 10f);
            verticalLinearGain[i] = Mathf.Pow(10f, -verticalRelativeAttenuation / 10f);
        }

        // Step 1 for Gil, done here to avoid repeating it for each evaluated direction
        for (int t = 0; t <= 180; t++)
        {
            frontVerticalLinearGain[t] = verticalLinearGain[t];
            backVerticalLinearGain[t] = verticalLinearGain[(t + 180) % 360];
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
                float gainLinear = EvaluateDirection(theta, phi);

                // Relative dB
                float gainDbRelative = 10f * Mathf.Log10(Mathf.Max(gainLinear, 1e-12f));

                // Absolute dBi
                float gainDbi;
                if (hasGain)
                {
                    gainDbi = gainMaxDbi + gainDbRelative;
                }
                else
                {
                    gainDbi = gainDbRelative;
                }

                // Save value in matrices
                GainLinearMatrix[theta, phi] = gainLinear;
                GainDbRelativeMatrix[theta, phi] = gainDbRelative;
                GainDbiMatrix[theta, phi] = gainDbi;
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
            float gainLinear = Mathf.Pow(Mathf.Sin(thetaRad), omniPowerP);

            // Applies floor
            gainLinear = Mathf.Lerp(omniFloor, 1f, gainLinear);

            // Gets relative dB from linear gain
            float gainDbRelative = 10f * Mathf.Log10(Mathf.Max(gainLinear, 1e-12f));

            for (int phi = 0; phi < 360; phi++)
            {
                GainLinearMatrix[theta, phi] = gainLinear;
                GainDbRelativeMatrix[theta, phi] = gainDbRelative;
                // Adds the configured maximum gain to convert relative dB into dBi
                GainDbiMatrix[theta, phi] = omniMaxGainDbi + gainDbRelative;
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
        float horizontalGainLinear = horizontalLinearGain[Wrap360(phiDeg)];

        // Vertical front
        float verticalFrontGainLinear = frontVerticalLinearGain[ClampTheta(thetaDeg)];

        // Vertical back
        float verticalBackGainLinear = backVerticalLinearGain[ClampTheta(thetaDeg)];

        // Poles
        float northPoleGainLinear = frontVerticalLinearGain[0];
        float southPoleGainLinear = frontVerticalLinearGain[180];

        // 3 - Choose hemisphere
        bool upper = thetaRad <= Mathf.PI / 2f;

        float theta1, theta2;
        float thetaBoundaryGainOne;
        float thetaBoundaryGainTwo;

        // 4 - Define distances in theta and limit values

        // For upper hemisphere
        if (upper)
        {
            theta1 = thetaRad;
            theta2 = (Mathf.PI / 2f) - thetaRad;
            thetaBoundaryGainOne = northPoleGainLinear;
            thetaBoundaryGainTwo = horizontalGainLinear;
        }
        else // For lower hemisphere
        {
            theta1 = thetaRad - (Mathf.PI / 2f);
            theta2 = Mathf.PI - thetaRad;
            thetaBoundaryGainOne = horizontalGainLinear;
            thetaBoundaryGainTwo = southPoleGainLinear;
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
            return verticalFrontGainLinear;
        }

        if (phi2 < eps)
        {
            return verticalBackGainLinear;
        }

        // Continuity factors
        float contTheta = (theta1 * theta2) / Mathf.Max((theta1 + theta2) * (theta1 + theta2), eps);
        float contPhi = (phi1 * phi2) / Mathf.Max((phi1 + phi2) * (phi1 + phi2), eps);

        // Main parts
        float phiContribution = (phi1 * verticalBackGainLinear + phi2 * verticalFrontGainLinear);
        float thetaContribution = (theta1 * thetaBoundaryGainTwo + theta2 * thetaBoundaryGainOne);

        // Final gain
        float numerator = phiContribution * contTheta + thetaContribution * contPhi;
        float denominator = (phi1 + phi2) * contTheta + (theta1 + theta2) * contPhi;

        // Avoids division by zero
        float gainLinear = numerator / Mathf.Max(denominator, eps);

        // Clamps to [0, 1] and handles NaN/Infinity
        if (float.IsNaN(gainLinear) || float.IsInfinity(gainLinear))
        {
            gainLinear = 0f;
        }

        return Mathf.Clamp01(gainLinear);
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
        float horizontalGainLinear = horizontalLinearGain[Wrap360(phiDeg)];
        float verticalGainLinear = verticalLinearGain[ClampTheta(thetaDeg)];

        // 2 - Cross weights
        float weightFromVertical = verticalGainLinear * (1f - horizontalGainLinear);
        float weightFromHorizontal = horizontalGainLinear * (1f - verticalGainLinear);

        // 3 - k-normalization
        float verticalWeightPower = Mathf.Pow(Mathf.Max(weightFromVertical, 0f), k);
        float horizontalWeightPower = Mathf.Pow(Mathf.Max(weightFromHorizontal, 0f), k);
        float denominator = Mathf.Pow(verticalWeightPower + horizontalWeightPower + 1e-12f, 1f / Mathf.Max(k, 0.001f));

        float verticalCoefficient = weightFromVertical / denominator;
        float horizontalCoefficient = weightFromHorizontal / denominator;

        // 4 - Combine in dB and back to linear

        // Combine
        float horizontalGainDb = 10f * Mathf.Log10(Mathf.Max(horizontalGainLinear, 1e-12f));
        float verticalGainDb = 10f * Mathf.Log10(Mathf.Max(verticalGainLinear, 1e-12f));
        float combinedGainDb = horizontalGainDb * verticalCoefficient + verticalGainDb * horizontalCoefficient;

        // Back to linear
        float gainLinear = Mathf.Pow(10f, combinedGainDb / 10f);

        if (float.IsNaN(gainLinear) || float.IsInfinity(gainLinear))
        {
            gainLinear = 0f;
        }

        return Mathf.Clamp01(gainLinear);
    }

    // --------------------------------------------------
    // HELPERS
    // --------------------------------------------------

    /// <summary>
    /// Returns the smallest value in an array.
    /// </summary>
    private static float MinArray(float[] array)
    {
        // Starts with a very large value
        float minimumValue = float.PositiveInfinity;

        // Checks all elements
        for (int i = 0; i < array.Length; i++)
        {
            minimumValue = Mathf.Min(minimumValue, array[i]);
        }

        return minimumValue;
    }

    /// <summary>
    /// Returns the index of the smallest value in an array.
    /// </summary>
    private static int ArgMin(float[] array)
    {
        // Starts assuming the first valid minimum
        int minimumIndex = 0;
        float minimumValue = float.PositiveInfinity;

        // Searches for the smallest value
        for (int i = 0; i < array.Length; i++)
        {
            if (array[i] < minimumValue)
            {
                minimumValue = array[i];
                minimumIndex = i;
            }
        }

        return minimumIndex;
    }

    /// <summary>
    /// Copies an array into another one with a circular shift.
    /// </summary>
    private static void CircularShiftInto(float[] sourceArray, float[] destinationArray, int shift)
    {
        int arrayLength = sourceArray.Length;

        for (int i = 0; i < arrayLength; i++)
        {
            // Computes shifted position
            int shiftedIndex = (i + shift) % arrayLength;

            // Fixes negative positions
            if (shiftedIndex < 0)
            {
                shiftedIndex += arrayLength;
            }

            destinationArray[shiftedIndex] = sourceArray[i];
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
    private static bool TryParseFloat(string text, out float value)
    {
        // Removes spaces and replaces comma with dot
        text = text.Trim().Replace(",", ".");

        return float.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value);
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
        Match floatMatch = Regex.Match(line, @"[-+]?\d+(?:[.,]\d+)?");

        if (!floatMatch.Success)
        {
            value = 0f;
            return false;
        }

        return TryParseFloat(floatMatch.Value, out value);
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
