using UnityEngine;
using UnityEngine.UI;

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