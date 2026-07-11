using TMPro;
using UnityEngine;

/// <summary>
/// Displays the minimum and maximum antenna gain represented by the pattern.
/// </summary>
public class PatternViewLegend : MonoBehaviour
{
    [Header("Source")]
    public PatternGainReconstructor reconstructor;

    [Header("UI")]
    public TMP_Text maxGainText;
    public TMP_Text minGainText;

    /// <summary>
    /// Updates the legend when the scene starts.
    /// </summary>
    void Start()
    {
        UpdateLegend();
    }

    /// <summary>
    /// Reads the gain matrix and updates the legend values.
    /// </summary>
    private void UpdateLegend()
    {
        // Uses the singleton if no reconstructor was assigned
        if (reconstructor == null)
        {
            reconstructor = PatternGainReconstructor.Instance;
        }

        if (reconstructor == null || !reconstructor.IsReady || reconstructor.GainDbiMatrix == null)
        {
            Debug.LogWarning("PatternViewLegend: Gain matrix is not ready.");
            return;
        }

        float[,] gainMatrix = reconstructor.GainDbiMatrix;

        float minGainDbi = float.PositiveInfinity;
        float maxGainDbi = float.NegativeInfinity;

        // Finds the complete gain range represented by the pattern
        for (int theta = 0; theta < gainMatrix.GetLength(0); theta++)
        {
            for (int phi = 0; phi < gainMatrix.GetLength(1); phi++)
            {
                float gainDbi = gainMatrix[theta, phi];

                minGainDbi = Mathf.Min(minGainDbi, gainDbi);
                maxGainDbi = Mathf.Max(maxGainDbi, gainDbi);
            }
        }

        // Omni colors use a fixed visual range so the legend matches the pattern mesh
        if (reconstructor.method == PatternGainReconstructor.ReconstructionMethod.Omni)
        {
            minGainDbi = maxGainDbi - 50f;
        }

        if (maxGainText != null)
        {
            maxGainText.text = $"{maxGainDbi:F2} dBi";
        }

        if (minGainText != null)
        {
            minGainText.text = $"{minGainDbi:F2} dBi";
        }
    }
}
