using System.Collections.Generic;
using System.Globalization;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class SimulationConfigMenuController : MonoBehaviour
{
    [Header("Panels")]
    public GameObject mainPanel;
    public GameObject configurationPanel;
    public GameObject antennaPropagationPanel;
    public GameObject gridAndReceiversPanel;
    public GameObject visualizationAndPerformancePanel;

    [Header("Antenna & Propagation")]
    public TMP_Dropdown methodDropdown;
    public GameObject kSliderRow;
    public Slider kSlider;
    public TMP_Text kValueText;
    public TMP_InputField txPowerInput;
    public TMP_InputField frequencyInput;
    public TMP_InputField bandwidthInput;
    public TMP_Dropdown scenarioDropdown;
    public TMP_Dropdown environmentDropdown;
    public GameObject nlosAlert;
    public TMP_Dropdown lossesModelDropdown;
    public Toggle disableShadowingToggle;

    [Header("Grid & Receivers")]
    public TMP_InputField gridSizeXInput;
    public TMP_InputField gridSizeYInput;
    public TMP_InputField gridSizeZInput;
    public TMP_Text voxelSizeValueText;
    public TMP_Text voxelCountText;
    public Toggle buildingCollisionsToggle;
    public TMP_InputField carRxGainInput;
    public TMP_InputField humanRxGainInput;


    [Header("Visualization & Performance")]
    public Slider minAlphaSlider;
    public TMP_Text minAlphaValueText;
    public Slider maxAlphaSlider;
    public TMP_Text maxAlphaValueText;
    public Slider alphaExponentSlider;
    public TMP_Text alphaExponentValueText;
    public TMP_Dropdown performanceModeDropdown;

    private float[] voxelSizes = new float[] { 0.1f, 0.2f, 0.25f, 0.5f, 1f, 2f, 4f, 8f };
    private int currentVoxelSizeIndex = 4;

    [Header("Input Validation")]
    public Color validInputColor = new Color32(5, 94, 239, 255);
    public Color invalidInputColor = new Color32(224, 0, 0, 255);

    void Start()
    {
        ConfigureControls();
        LoadConfig();
        RefreshAll();
        ShowMainPanel();
    }

    private void ConfigureControls()
    {
        // Dropdown options shown in the menu
        methodDropdown.ClearOptions();
        methodDropdown.AddOptions(new List<string> { "Vasiliadis2005", "Gil2001", "Omni" });

        scenarioDropdown.ClearOptions();
        scenarioDropdown.AddOptions(new List<string> { "Umi", "UMa", "Indoor" });

        environmentDropdown.ClearOptions();
        environmentDropdown.AddOptions(new List<string> { "LOS", "NLOS" });

        lossesModelDropdown.ClearOptions();
        lossesModelDropdown.AddOptions(new List<string> { "ABG", "FSPL" });

        performanceModeDropdown.ClearOptions();
        performanceModeDropdown.AddOptions(new List<string> { "Low", "Medium", "High" });

        // Vasiliadis factor. Only used when the selected method is Vasiliadis
        kSlider.minValue = 0.5f;
        kSlider.maxValue = 10f;
        kSlider.wholeNumbers = false;

        // Alpha sliders
        minAlphaSlider.minValue = 0f;
        minAlphaSlider.maxValue = 1f;
        minAlphaSlider.wholeNumbers = false;

        maxAlphaSlider.minValue = 0f;
        maxAlphaSlider.maxValue = 1f;
        maxAlphaSlider.wholeNumbers = false;

        alphaExponentSlider.minValue = 1f;
        alphaExponentSlider.maxValue = 10f;
        alphaExponentSlider.wholeNumbers = false;

        // UI events
        methodDropdown.onValueChanged.AddListener(OnMethodChanged);
        kSlider.onValueChanged.AddListener(OnKSliderChanged);
        environmentDropdown.onValueChanged.AddListener(OnEnvironmentChanged);
        minAlphaSlider.onValueChanged.AddListener(OnMinAlphaSliderChanged);
        maxAlphaSlider.onValueChanged.AddListener(OnMaxAlphaSliderChanged);
        alphaExponentSlider.onValueChanged.AddListener(OnAlphaExponentSliderChanged);

        gridSizeXInput.onValueChanged.AddListener(OnGridInputChanged);
        gridSizeYInput.onValueChanged.AddListener(OnGridInputChanged);
        gridSizeZInput.onValueChanged.AddListener(OnGridInputChanged);
    }

    private void LoadConfig()
    {

        if (SimulationConfig.reconstructionMethod == PatternGainReconstructor.ReconstructionMethod.Vasiliadis2005)
        {
            methodDropdown.value = 0;
        }
        else if (SimulationConfig.reconstructionMethod == PatternGainReconstructor.ReconstructionMethod.Gil2001)
        {
            methodDropdown.value = 1;
        }
        else
        {
            methodDropdown.value = 2;
        }

        kSlider.value = SimulationConfig.k;

        txPowerInput.text = FormatFloat(SimulationConfig.txPowerDbm, "F2");
        frequencyInput.text = FormatFloat(SimulationConfig.frequencyGHz, "F3");
        bandwidthInput.text = FormatFloat(SimulationConfig.bandwidthMHz, "F2");

        scenarioDropdown.value = (int)SimulationConfig.scenario;
        environmentDropdown.value = (int)SimulationConfig.environmentType;
        lossesModelDropdown.value = (int)SimulationConfig.lossesModel;
        disableShadowingToggle.isOn = SimulationConfig.disableShadowing;

        gridSizeXInput.text = SimulationConfig.gridSizeMeters.x.ToString(CultureInfo.InvariantCulture);
        gridSizeYInput.text = SimulationConfig.gridSizeMeters.y.ToString(CultureInfo.InvariantCulture);
        gridSizeZInput.text = SimulationConfig.gridSizeMeters.z.ToString(CultureInfo.InvariantCulture);

        currentVoxelSizeIndex = FindVoxelSizeIndex(SimulationConfig.voxelSizeMeters);
        buildingCollisionsToggle.isOn = SimulationConfig.buildingCollisions;

        carRxGainInput.text = FormatFloat(SimulationConfig.carRxGainDbi, "F2");
        humanRxGainInput.text = FormatFloat(SimulationConfig.humanRxGainDbi, "F2");

        minAlphaSlider.value = SimulationConfig.minAlpha;
        maxAlphaSlider.value = SimulationConfig.maxAlpha;
        alphaExponentSlider.value = SimulationConfig.alphaExponent;

        performanceModeDropdown.value = (int)SimulationConfig.performanceMode;
    }

    public void ShowMainPanel()
    {
        ShowOnly(mainPanel);
    }

    public void ShowAntennaPropagationPanel()
    {
        ShowOnly(antennaPropagationPanel);
    }

    public void ShowGridAndReceiversPanel()
    {
        if (!ValidateAntennaPropagationInputs())
        {
            return;
        }

        ShowOnly(gridAndReceiversPanel);
    }

    public void ShowVisualizationAndPerformancePanel()
    {
        if (!ValidateGridAndReceiverInputs())
        {
            return;
        }

        ShowOnly(visualizationAndPerformancePanel);
    }

    public void StartSimulation()
    {
        if (!ValidateAllInputs())
        {
            return;
        }

        SaveUiIntoConfig();
        SceneManager.LoadScene("SimulationScene");
    }

    public void ExitApplication()
    {
        Application.Quit();
    }

    public void PreviousVoxelSize()
    {
        currentVoxelSizeIndex--;

        if (currentVoxelSizeIndex < 0)
        {
            currentVoxelSizeIndex = voxelSizes.Length - 1;
        }

        RefreshVoxelSizeText();
        RefreshVoxelCount();
    }

    public void NextVoxelSize()
    {
        currentVoxelSizeIndex++;

        if (currentVoxelSizeIndex >= voxelSizes.Length)
        {
            currentVoxelSizeIndex = 0;
        }

        RefreshVoxelSizeText();
        RefreshVoxelCount();
    }

    private void SaveUiIntoConfig()
    {
        if (methodDropdown.value == 0)
        {
            SimulationConfig.reconstructionMethod = PatternGainReconstructor.ReconstructionMethod.Vasiliadis2005;
        }
        else if (methodDropdown.value == 1)
        {
            SimulationConfig.reconstructionMethod = PatternGainReconstructor.ReconstructionMethod.Gil2001;
        }
        else
        {
            SimulationConfig.reconstructionMethod = PatternGainReconstructor.ReconstructionMethod.Omni;
        }

        SimulationConfig.k = Mathf.Clamp(kSlider.value, 0.5f, 10f);

        float txPowerDbm;
        float frequencyGHz;
        float bandwidthMHz;
        float carRxGainDbi;
        float humanRxGainDbi;

        TryReadDecimal(txPowerInput, out txPowerDbm);
        TryReadDecimal(frequencyInput, out frequencyGHz);
        TryReadDecimal(bandwidthInput, out bandwidthMHz);
        TryReadDecimal(carRxGainInput, out carRxGainDbi);
        TryReadDecimal(humanRxGainInput, out humanRxGainDbi);

        SimulationConfig.txPowerDbm = txPowerDbm;

        SimulationConfig.frequencyGHz = frequencyGHz;
        SimulationConfig.frequencyGHz = Mathf.Max(0.001f, SimulationConfig.frequencyGHz);

        SimulationConfig.bandwidthMHz = bandwidthMHz;
        SimulationConfig.bandwidthMHz = Mathf.Max(0.001f, SimulationConfig.bandwidthMHz);

        SimulationConfig.scenario = (PropagationSettings.ScenarioType)scenarioDropdown.value;
        SimulationConfig.environmentType = (PropagationSettings.EnvironmentType)environmentDropdown.value;
        SimulationConfig.lossesModel = (PropagationSettings.LossesModelType)lossesModelDropdown.value;
        SimulationConfig.disableShadowing = disableShadowingToggle.isOn;

        int gridX = ReadInt(gridSizeXInput, SimulationConfig.gridSizeMeters.x);
        int gridY = ReadInt(gridSizeYInput, SimulationConfig.gridSizeMeters.y);
        int gridZ = ReadInt(gridSizeZInput, SimulationConfig.gridSizeMeters.z);

        gridX = Mathf.Max(1, gridX);
        gridY = Mathf.Max(1, gridY);
        gridZ = Mathf.Max(1, gridZ);

        SimulationConfig.gridSizeMeters = new Vector3Int(gridX, gridY, gridZ);
        SimulationConfig.voxelSizeMeters = voxelSizes[currentVoxelSizeIndex];
        SimulationConfig.buildingCollisions = buildingCollisionsToggle.isOn;

        SimulationConfig.carRxGainDbi = carRxGainDbi;
        SimulationConfig.humanRxGainDbi = humanRxGainDbi;

        SimulationConfig.minAlpha = minAlphaSlider.value;
        SimulationConfig.maxAlpha = maxAlphaSlider.value;
        SimulationConfig.alphaExponent = alphaExponentSlider.value;

        SimulationConfig.performanceMode = (PerformanceSettingsManager.PerformanceMode)performanceModeDropdown.value;
    }

    private void ShowOnly(GameObject activePanel)
    {
        mainPanel.SetActive(activePanel == mainPanel);
        configurationPanel.SetActive(activePanel != mainPanel);
        antennaPropagationPanel.SetActive(activePanel == antennaPropagationPanel);
        gridAndReceiversPanel.SetActive(activePanel == gridAndReceiversPanel);
        visualizationAndPerformancePanel.SetActive(activePanel == visualizationAndPerformancePanel);
    }

    private void RefreshAll()
    {
        RefreshMethodUi();
        RefreshVoxelSizeText();
        RefreshAlphaSliders(false);
        RefreshSliderTexts();
        RefreshVoxelCount();
    }

    private void RefreshMethodUi()
    {
        // K only affects the Vasiliadis method
        if (methodDropdown.value == 0)
        {
            kSliderRow.SetActive(true);
        }
        else
        {
            kSliderRow.SetActive(false);
        }
    }

    private void RefreshEnvironmentUi()
    {
        if (environmentDropdown.value == 1)
        {
            nlosAlert.SetActive(true);
        }
        else
        {
            nlosAlert.SetActive(false);
        }
    }

    private void RefreshVoxelSizeText()
    {
        float voxelSize = voxelSizes[currentVoxelSizeIndex];
        voxelSizeValueText.text = FormatFloat(voxelSize, "0.##") + " m";
    }

    private void RefreshAlphaSliders(bool changedMinAlpha)
    {
        float minimumGap = 0.01f;

        float minAlpha = Mathf.Clamp01(minAlphaSlider.value);
        float maxAlpha = Mathf.Clamp01(maxAlphaSlider.value);

        // Min alpha must always be lower than max alpha
        if (minAlpha >= maxAlpha)
        {
            if (changedMinAlpha)
            {
                minAlpha = maxAlpha - minimumGap;
            }
            else
            {
                maxAlpha = minAlpha + minimumGap;
            }
        }

        minAlpha = Mathf.Clamp(minAlpha, 0f, 1f - minimumGap);
        maxAlpha = Mathf.Clamp(maxAlpha, minimumGap, 1f);

        if (minAlpha >= maxAlpha)
        {
            minAlpha = 0f;
            maxAlpha = minimumGap;
        }

        minAlphaSlider.SetValueWithoutNotify(minAlpha);
        maxAlphaSlider.SetValueWithoutNotify(maxAlpha);

        RefreshSliderTexts();
    }

    private void RefreshSliderTexts()
    {
        kValueText.text = FormatFloat(kSlider.value, "F2");
        minAlphaValueText.text = FormatFloat(minAlphaSlider.value, "F2");
        maxAlphaValueText.text = FormatFloat(maxAlphaSlider.value, "F2");
        alphaExponentValueText.text = FormatFloat(alphaExponentSlider.value, "F2");
    }

    private void RefreshVoxelCount()
    {
        int gridX;
        int gridY;
        int gridZ;

        if (!TryReadInteger(gridSizeXInput, out gridX))
        {
            voxelCountText.text = "Voxel count: 0";
            return;
        }

        if (!TryReadInteger(gridSizeYInput, out gridY))
        {
            voxelCountText.text = "Voxel count: 0";
            return;
        }

        if (!TryReadInteger(gridSizeZInput, out gridZ))
        {
            voxelCountText.text = "Voxel count: 0";
            return;
        }

        if (gridX < 1 || gridY < 1 || gridZ < 1)
        {
            voxelCountText.text = "Voxel count: 0";
            return;
        }

        float voxelSize = voxelSizes[currentVoxelSizeIndex];

        int voxelCountX = Mathf.CeilToInt(gridX / voxelSize);
        int voxelCountY = Mathf.CeilToInt(gridY / voxelSize);
        int voxelCountZ = Mathf.CeilToInt(gridZ / voxelSize);

        long totalVoxelCount = (long)voxelCountX * voxelCountY * voxelCountZ;

        voxelCountText.text = "Voxel count: " + totalVoxelCount;
    }

    private bool ValidateAllInputs()
    {
        bool antennaInputsValid = ValidateAntennaPropagationInputs();
        bool gridInputsValid = ValidateGridAndReceiverInputs();

        if (!antennaInputsValid)
        {
            return false;
        }

        if (!gridInputsValid)
        {
            return false;
        }

        return true;
    }

    private bool ValidateAntennaPropagationInputs()
    {
        bool allValid = true;
        float value;

        // Tx power can be positive, zero, or negative in dBm
        bool txPowerValid = TryReadDecimal(txPowerInput, out value);
        SetInputValid(txPowerInput, txPowerValid);

        if (!txPowerValid)
        {
            allValid = false;
        }

        // Frequency must be greater than zero
        bool frequencyValid = TryReadDecimal(frequencyInput, out value);

        if (frequencyValid && value <= 0f)
        {
            frequencyValid = false;
        }

        SetInputValid(frequencyInput, frequencyValid);

        if (!frequencyValid)
        {
            allValid = false;
        }

        // Bandwidth must be greater than zero
        bool bandwidthValid = TryReadDecimal(bandwidthInput, out value);

        if (bandwidthValid && value <= 0f)
        {
            bandwidthValid = false;
        }

        SetInputValid(bandwidthInput, bandwidthValid);

        if (!bandwidthValid)
        {
            allValid = false;
        }

        return allValid;
    }

    private bool ValidateGridAndReceiverInputs()
    {
        bool allValid = true;
        int gridValue;
        float gainValue;

        // Grid X must be between 1 and 500 meters
        bool gridXValid = TryReadInteger(gridSizeXInput, out gridValue);

        if (gridXValid && gridValue < 1)
        {
            gridXValid = false;
        }

        if (gridXValid && gridValue > 500)
        {
            gridXValid = false;
        }

        SetInputValid(gridSizeXInput, gridXValid);

        if (!gridXValid)
        {
            allValid = false;
        }

        // Grid Y must be between 1 and 200 meters
        bool gridYValid = TryReadInteger(gridSizeYInput, out gridValue);

        if (gridYValid && gridValue < 1)
        {
            gridYValid = false;
        }

        if (gridYValid && gridValue > 200)
        {
            gridYValid = false;
        }

        SetInputValid(gridSizeYInput, gridYValid);

        if (!gridYValid)
        {
            allValid = false;
        }

        // Grid Z must be between 1 and 500 meters
        bool gridZValid = TryReadInteger(gridSizeZInput, out gridValue);

        if (gridZValid && gridValue < 1)
        {
            gridZValid = false;
        }

        if (gridZValid && gridValue > 500)
        {
            gridZValid = false;
        }

        SetInputValid(gridSizeZInput, gridZValid);

        if (!gridZValid)
        {
            allValid = false;
        }

        // Receiver gains can be positive, zero, or negative in dBi
        bool carGainValid = TryReadDecimal(carRxGainInput, out gainValue);
        SetInputValid(carRxGainInput, carGainValid);

        if (!carGainValid)
        {
            allValid = false;
        }

        bool humanGainValid = TryReadDecimal(humanRxGainInput, out gainValue);
        SetInputValid(humanRxGainInput, humanGainValid);

        if (!humanGainValid)
        {
            allValid = false;
        }

        return allValid;
    }

    private bool TryReadInteger(TMP_InputField input, out int value)
    {
        value = 0;

        if (input == null)
        {
            return false;
        }

        string text = input.text.Trim();

        if (string.IsNullOrEmpty(text))
        {
            return false;
        }

        if (!int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out value))
        {
            return false;
        }

        return true;
    }

    private bool TryReadDecimal(TMP_InputField input, out float value)
    {
        value = 0f;

        if (input == null)
        {
            return false;
        }

        string text = input.text.Trim();

        if (string.IsNullOrEmpty(text))
        {
            return false;
        }

        // The simulator uses English decimal format, so commas are not valid
        if (text.Contains(","))
        {
            return false;
        }

        if (!float.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value))
        {
            return false;
        }

        if (float.IsNaN(value) || float.IsInfinity(value))
        {
            return false;
        }

        return true;
    }

    private void SetInputValid(TMP_InputField input, bool valid)
    {
        if (input == null)
        {
            return;
        }

        Image inputImage = input.GetComponent<Image>();

        if (inputImage == null)
        {
            return;
        }

        if (valid)
        {
            inputImage.color = validInputColor;
        }
        else
        {
            inputImage.color = invalidInputColor;
        }
    }

    private int ReadInt(TMP_InputField input, int defaultValue)
    {
        if (input == null)
        {
            return defaultValue;
        }

        int value;

        if (int.TryParse(input.text, NumberStyles.Integer, CultureInfo.InvariantCulture, out value))
        {
            return value;
        }

        return defaultValue;
    }

    private int FindVoxelSizeIndex(float value)
    {
        for (int i = 0; i < voxelSizes.Length; i++)
        {
            if (Mathf.Approximately(voxelSizes[i], value))
            {
                return i;
            }
        }

        return 0;
    }

    private string FormatFloat(float value, string format)
    {
        return value.ToString(format, CultureInfo.InvariantCulture);
    }

    private void OnMethodChanged(int value)
    {
        RefreshMethodUi();
    }

    private void OnKSliderChanged(float value)
    {
        float roundedValue = Mathf.Round(value / 0.05f) * 0.05f;

        if (!Mathf.Approximately(kSlider.value, roundedValue))
        {
            kSlider.SetValueWithoutNotify(roundedValue);
        }

        RefreshSliderTexts();
    }

    private void OnMinAlphaSliderChanged(float value)
    {
        RefreshAlphaSliders(true);
    }

    private void OnMaxAlphaSliderChanged(float value)
    {
        RefreshAlphaSliders(false);
    }

    private void OnAlphaExponentSliderChanged(float value)
    {
        RefreshSliderTexts();
    }

    private void OnGridInputChanged(string value)
    {
        RefreshVoxelCount();
    }

    private void OnEnvironmentChanged(int value)
    {
        RefreshEnvironmentUi();
    }
}
