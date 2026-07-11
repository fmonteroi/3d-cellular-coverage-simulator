using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Applies performance modes by enabling or disabling optional scene groups.
/// </summary>
public class PerformanceSettingsManager : MonoBehaviour
{
    public enum PerformanceMode
    {
        Low,
        Medium,
        High
    }

    [Header("UI")]
    public Toggle lowToggle;
    public Toggle mediumToggle;
    public Toggle highToggle;

    [Header("Default")]
    public PerformanceMode defaultMode = PerformanceMode.High;

    [Header("Scene groups")]
    public GameObject vegetation;
    public GameObject park;
    public GameObject background;

    /// <summary>
    /// Registers toggle callbacks and applies the default mode.
    /// </summary>
    void Start()
    {
        if (lowToggle != null)
        {
            lowToggle.onValueChanged.AddListener(isOn =>
            {
                if (isOn)
                {
                    ApplyPerformanceMode(PerformanceMode.Low);
                }
            });
        }

        if (mediumToggle != null)
        {
            mediumToggle.onValueChanged.AddListener(isOn =>
            {
                if (isOn)
                {
                    ApplyPerformanceMode(PerformanceMode.Medium);
                }
            });
        }

        if (highToggle != null)
        {
            highToggle.onValueChanged.AddListener(isOn =>
            {
                if (isOn)
                {
                    ApplyPerformanceMode(PerformanceMode.High);
                }
            });
        }

        SetInitialMode();
    }

    /// <summary>
    /// Updates toggle states and applies the selected initial mode.
    /// </summary>
    private void SetInitialMode()
    {
        if (lowToggle != null)
        {
            lowToggle.isOn = defaultMode == PerformanceMode.Low;
        }

        if (mediumToggle != null)
        {
            mediumToggle.isOn = defaultMode == PerformanceMode.Medium;
        }

        if (highToggle != null)
        {
            highToggle.isOn = defaultMode == PerformanceMode.High;
        }

        ApplyPerformanceMode(defaultMode);
    }

    /// <summary>
    /// Enables scene groups according to the selected performance mode.
    /// </summary>
    private void ApplyPerformanceMode(PerformanceMode mode)
    {
        bool showVegetation = true;
        bool showPark = true;
        bool showBackground = true;

        if (mode == PerformanceMode.Medium)
        {
            showVegetation = false;
        }

        if (mode == PerformanceMode.High)
        {
            showVegetation = false;
            showPark = false;
            showBackground = false;
        }

        if (vegetation != null)
        {
            vegetation.SetActive(showVegetation);
        }

        if (park != null)
        {
            park.SetActive(showPark);
        }

        if (background != null)
        {
            background.SetActive(showBackground);
        }
    }
}
