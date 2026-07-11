using UnityEngine;

/// <summary>
/// Limits the application frame rate to the monitor refresh rate or a maximum value.
/// </summary>
public class FrameRateLimiter : MonoBehaviour
{
    public int maxFrameRate = 120;

    /// <summary>
    /// Applies the frame rate limit when the scene starts.
    /// </summary>
    void Awake()
    {
        int refreshRate = Mathf.RoundToInt((float)Screen.currentResolution.refreshRateRatio.value);
        int targetFrameRate = Mathf.Min(refreshRate, maxFrameRate);

        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = targetFrameRate;
    }
}