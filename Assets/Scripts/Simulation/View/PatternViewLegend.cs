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

    void Start()
    {
        UpdateLegend();
    }

    /// <summary>
    /// Reads the gain matrix and updates the legend values.
    /// </summary>
    private void UpdateLegend()
    {
        // Use the singleton if no reconstructor was assigned
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

        // Find the complete gain range represented by the pattern
        for (int theta = 0; theta < gainMatrix.GetLength(0); theta++)
        {
            for (int phi = 0; phi < gainMatrix.GetLength(1); phi++)
            {
                float gainDbi = gainMatrix[theta, phi];

                minGainDbi = Mathf.Min(minGainDbi, gainDbi);
                maxGainDbi = Mathf.Max(maxGainDbi, gainDbi);
            }
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