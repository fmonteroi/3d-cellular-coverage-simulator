using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

public class MainMenuUi : MonoBehaviour
{
    [Header("Panels")]
    public GameObject mainPanel;
    public GameObject configPanel;

    [Header("Value Texts")]
    public TextMeshProUGUI mapValueText;
    public TextMeshProUGUI vehicleValueText;
    public TextMeshProUGUI pedestrianValueText;

    [Header("Maps")]
    public string[] mapNames;

    [Header("Limits")]
    public int minVehicles = 0;
    public int maxVehicles = 5;
    public int minPedestrians = 0;
    public int maxPedestrians = 5;

    private void Start()
    {
        mainPanel.SetActive(true);
        configPanel.SetActive(false);
        RefreshUIValues();
    }

    public void OpenConfigPanel()
    {
        mainPanel.SetActive(false);
        configPanel.SetActive(true);
        RefreshUIValues();
    }

    public void BackToMainPanel()
    {
        configPanel.SetActive(false);
        mainPanel.SetActive(true);
        // No need to refresh values because they aren't shown in the main panel
    }

    public void NextMap()
    {
        if (mapNames == null || mapNames.Length == 0) return;

        SimulationConfig.selectedMapIndex++;
        if (SimulationConfig.selectedMapIndex >= mapNames.Length)
            SimulationConfig.selectedMapIndex = 0;

        RefreshUIValues();
    }

    public void PreviousMap()
    {
        if (mapNames == null || mapNames.Length == 0) return;

        SimulationConfig.selectedMapIndex--;
        if (SimulationConfig.selectedMapIndex < 0)
            SimulationConfig.selectedMapIndex = mapNames.Length - 1;

        RefreshUIValues();
    }

    public void IncreaseVehicles()
    {
        SimulationConfig.vehicleCount++;
        // Makes sure vehicle count stays within the limits
        SimulationConfig.vehicleCount = Mathf.Clamp(SimulationConfig.vehicleCount, minVehicles, maxVehicles);
        RefreshUIValues();
    }

    public void DecreaseVehicles()
    {
        SimulationConfig.vehicleCount--;
        // Makes sure vehicle count stays within the limits
        SimulationConfig.vehicleCount = Mathf.Clamp(SimulationConfig.vehicleCount, minVehicles, maxVehicles);
        RefreshUIValues();
    }

    public void IncreasePedestrians()
    {
        SimulationConfig.pedestrianCount++;
        // Makes sure pedestrian count stays within the limits
        SimulationConfig.pedestrianCount = Mathf.Clamp(SimulationConfig.pedestrianCount, minPedestrians, maxPedestrians);
        RefreshUIValues();
    }

    public void DecreasePedestrians()
    {
        SimulationConfig.pedestrianCount--;
        // Makes sure pedestrian count stays within the limits
        SimulationConfig.pedestrianCount = Mathf.Clamp(SimulationConfig.pedestrianCount, minPedestrians, maxPedestrians);
        RefreshUIValues();
    }

    public void StartSimulation()
    {
        SceneManager.LoadScene("SimulationScene");
    }

    public void ExitApplication()
    {
        Application.Quit();
    }

    private void RefreshUIValues()
    {
        if (mapNames != null && mapNames.Length > 0)
        {
            mapValueText.text = mapNames[SimulationConfig.selectedMapIndex];
        }
        else
        {
            mapValueText.text = "Sin mapas";
        }

        vehicleValueText.text = SimulationConfig.vehicleCount.ToString();
        pedestrianValueText.text = SimulationConfig.pedestrianCount.ToString();
    }
}