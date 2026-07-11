using System.Collections.Generic;
using System.Globalization;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

/// <summary>
/// Controls the main menu configuration flow and stores the selected simulation values.
/// </summary>
public class SimulationConfigMenuController : MonoBehaviour
{
    [Header("Panels")]
    public GameObject mainPanel;
    public GameObject configurationPanel;
    public GameObject antennaPropagationPanel;
    public GameObject gridAndReceiversPanel;
    public GameObject visualizationAndPerformancePanel;
    public GameObject resultsAndGraphsPanel;

    [Header("Antenna & Propagation")]
    public TMP_Dropdown methodDropdown;
    public GameObject kSliderRow;
    public Slider kSlider;
    public TMP_Text kValueText;
    public GameObject omniMaxGainRow;
    public TMP_InputField omniMaxGainInput;
    public TMP_InputField txPowerInput;
    public TMP_InputField frequencyInput;
    public TMP_InputField bandwidthInput;
    public GameObject scenarioRow;
    public TMP_Dropdown scenarioDropdown;
    public GameObject environmentRow;
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
    public TMP_InputField vehicularRxGainInput;
    public TMP_InputField cellularRxGainInput;


    [Header("Visualization & Performance")]
    public Slider minAlphaSlider;
    public TMP_Text minAlphaValueText;
    public Slider maxAlphaSlider;
    public TMP_Text maxAlphaValueText;
    public Slider alphaExponentSlider;
    public TMP_Text alphaExponentValueText;
    public TMP_Dropdown performanceModeDropdown;

    [Header("Results & Graphs")]
    public Toggle campusVehiclePrxDistanceToggle;
    public Toggle campusVehicleSnrDistanceToggle;
    public Toggle campusVehicleSnrTimeToggle;
    public Toggle pedestrianPrxDistanceToggle;
    public Toggle pedestrianSnrDistanceToggle;
    public Toggle pedestrianSnrTimeToggle;
    public Toggle linearVehiclePrxDistanceToggle;
    public Toggle linearVehicleSnrDistanceToggle;
    public Toggle linearVehicleSnrTimeToggle;

    private float[] voxelSizes = new float[] { 0.1f, 0.2f, 0.25f, 0.5f, 1f, 2f, 4f, 8f };
    private int currentVoxelSizeIndex = 4;

    [Header("Input Validation")]
    public Color validInputColor = new Color32(5, 94, 239, 255);
    public Color invalidInputColor = new Color32(224, 0, 0, 255);

    /// <summary>
    /// Initializes controls, loads saved values and shows the main panel.
    /// </summary>
    void Start()
    {
        ConfigureControls();
        LoadConfig();
        RefreshAll();
        ShowMainPanel();
    }

    /// <summary>
    /// Configures dropdown options, slider ranges and UI callbacks.
    /// </summary>
    private void ConfigureControls()
    {
        // Sets dropdown options shown in the menu
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

        // Configures the Vasiliadis factor slider
        kSlider.minValue = 0.5f;
        kSlider.maxValue = 10f;
        kSlider.wholeNumbers = false;

        // Configures alpha sliders
        minAlphaSlider.minValue = 0f;
        minAlphaSlider.maxValue = 1f;
        minAlphaSlider.wholeNumbers = false;

        maxAlphaSlider.minValue = 0f;
        maxAlphaSlider.maxValue = 1f;
        maxAlphaSlider.wholeNumbers = false;

        alphaExponentSlider.minValue = 1f;
        alphaExponentSlider.maxValue = 10f;
        alphaExponentSlider.wholeNumbers = false;

        // Registers UI events
        methodDropdown.onValueChanged.AddListener(OnMethodChanged);
        kSlider.onValueChanged.AddListener(OnKSliderChanged);
        environmentDropdown.onValueChanged.AddListener(OnEnvironmentChanged);
        lossesModelDropdown.onValueChanged.AddListener(OnLossesModelChanged);
        minAlphaSlider.onValueChanged.AddListener(OnMinAlphaSliderChanged);
        maxAlphaSlider.onValueChanged.AddListener(OnMaxAlphaSliderChanged);
        alphaExponentSlider.onValueChanged.AddListener(OnAlphaExponentSliderChanged);

        gridSizeXInput.onValueChanged.AddListener(OnGridInputChanged);
        gridSizeYInput.onValueChanged.AddListener(OnGridInputChanged);
        gridSizeZInput.onValueChanged.AddListener(OnGridInputChanged);
    }

    /// <summary>
    /// Loads the current static simulation configuration into the menu controls.
    /// </summary>
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

        if (omniMaxGainInput != null)
        {
            omniMaxGainInput.text = FormatFloat(SimulationConfig.omniMaxGainDbi, "F2");
        }

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

        vehicularRxGainInput.text = FormatFloat(SimulationConfig.vehicularRxGainDbi, "F2");
        cellularRxGainInput.text = FormatFloat(SimulationConfig.cellularRxGainDbi, "F2");

        minAlphaSlider.value = SimulationConfig.minAlpha;
        maxAlphaSlider.value = SimulationConfig.maxAlpha;
        alphaExponentSlider.value = SimulationConfig.alphaExponent;

        performanceModeDropdown.value = (int)SimulationConfig.performanceMode;

        campusVehiclePrxDistanceToggle.isOn = SimulationConfig.campusVehicleGraphs.prxDistance;
        campusVehicleSnrDistanceToggle.isOn = SimulationConfig.campusVehicleGraphs.snrDistance;
        campusVehicleSnrTimeToggle.isOn = SimulationConfig.campusVehicleGraphs.snrTime;

        pedestrianPrxDistanceToggle.isOn = SimulationConfig.pedestrianGraphs.prxDistance;
        pedestrianSnrDistanceToggle.isOn = SimulationConfig.pedestrianGraphs.snrDistance;
        pedestrianSnrTimeToggle.isOn = SimulationConfig.pedestrianGraphs.snrTime;

        linearVehiclePrxDistanceToggle.isOn = SimulationConfig.linearVehicleGraphs.prxDistance;
        linearVehicleSnrDistanceToggle.isOn = SimulationConfig.linearVehicleGraphs.snrDistance;
        linearVehicleSnrTimeToggle.isOn = SimulationConfig.linearVehicleGraphs.snrTime;
    }

    /// <summary>
    /// Shows the initial menu panel.
    /// </summary>
    public void ShowMainPanel()
    {
        ShowOnly(mainPanel);
    }

    /// <summary>
    /// Shows the antenna and propagation configuration panel.
    /// </summary>
    public void ShowAntennaPropagationPanel()
    {
        ShowOnly(antennaPropagationPanel);
    }

    /// <summary>
    /// Validates antenna inputs and shows the grid and receiver panel.
    /// </summary>
    public void ShowGridAndReceiversPanel()
    {
        if (!ValidateAntennaPropagationInputs())
        {
            return;
        }

        ShowOnly(gridAndReceiversPanel);
    }

    /// <summary>
    /// Validates grid and receiver inputs and shows the visualization panel.
    /// </summary>
    public void ShowVisualizationAndPerformancePanel()
    {
        if (!ValidateGridAndReceiverInputs())
        {
            return;
        }

        ShowOnly(visualizationAndPerformancePanel);
    }

    /// <summary>
    /// Shows the result graph selection panel.
    /// </summary>
    public void ShowResultsAndGraphsPanel()
    {
        ShowOnly(resultsAndGraphsPanel);
    }

    /// <summary>
    /// Validates every input, saves the menu values and loads the simulation scene.
    /// </summary>
    public void StartSimulation()
    {
        if (!ValidateAllInputs())
        {
            return;
        }

        SaveUiIntoConfig();
        SceneManager.LoadScene("SimulationScene");
    }

    /// <summary>
    /// Closes the application build.
    /// </summary>
    public void ExitApplication()
    {
        Application.Quit();
    }

    /// <summary>
    /// Selects the previous voxel size from the fixed list.
    /// </summary>
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

    /// <summary>
    /// Selects the next voxel size from the fixed list.
    /// </summary>
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

    /// <summary>
    /// Copies the current UI values into the static simulation configuration.
    /// </summary>
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
        float omniMaxGainDbi;
        float vehicularRxGainDbi;
        float cellularRxGainDbi;

        TryReadDecimal(omniMaxGainInput, out omniMaxGainDbi);
        TryReadDecimal(txPowerInput, out txPowerDbm);
        TryReadDecimal(frequencyInput, out frequencyGHz);
        TryReadDecimal(bandwidthInput, out bandwidthMHz);
        TryReadDecimal(vehicularRxGainInput, out vehicularRxGainDbi);
        TryReadDecimal(cellularRxGainInput, out cellularRxGainDbi);

        SimulationConfig.omniMaxGainDbi = omniMaxGainDbi;

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

        SimulationConfig.vehicularRxGainDbi = vehicularRxGainDbi;
        SimulationConfig.cellularRxGainDbi = cellularRxGainDbi;

        SimulationConfig.minAlpha = minAlphaSlider.value;
        SimulationConfig.maxAlpha = maxAlphaSlider.value;
        SimulationConfig.alphaExponent = alphaExponentSlider.value;

        SimulationConfig.performanceMode = (PerformanceSettingsManager.PerformanceMode)performanceModeDropdown.value;

        SimulationConfig.campusVehicleGraphs.prxDistance = campusVehiclePrxDistanceToggle.isOn;
        SimulationConfig.campusVehicleGraphs.snrDistance = campusVehicleSnrDistanceToggle.isOn;
        SimulationConfig.campusVehicleGraphs.snrTime = campusVehicleSnrTimeToggle.isOn;

        SimulationConfig.pedestrianGraphs.prxDistance = pedestrianPrxDistanceToggle.isOn;
        SimulationConfig.pedestrianGraphs.snrDistance = pedestrianSnrDistanceToggle.isOn;
        SimulationConfig.pedestrianGraphs.snrTime = pedestrianSnrTimeToggle.isOn;

        SimulationConfig.linearVehicleGraphs.prxDistance = linearVehiclePrxDistanceToggle.isOn;
        SimulationConfig.linearVehicleGraphs.snrDistance = linearVehicleSnrDistanceToggle.isOn;
        SimulationConfig.linearVehicleGraphs.snrTime = linearVehicleSnrTimeToggle.isOn;
    }

    /// <summary>
    /// Activates only the requested configuration panel.
    /// </summary>
    private void ShowOnly(GameObject activePanel)
    {
        mainPanel.SetActive(activePanel == mainPanel);
        configurationPanel.SetActive(activePanel != mainPanel);
        antennaPropagationPanel.SetActive(activePanel == antennaPropagationPanel);
        gridAndReceiversPanel.SetActive(activePanel == gridAndReceiversPanel);
        visualizationAndPerformancePanel.SetActive(activePanel == visualizationAndPerformancePanel);
        resultsAndGraphsPanel.SetActive(activePanel == resultsAndGraphsPanel);
    }

    /// <summary>
    /// Refreshes all dynamic UI elements after loading values.
    /// </summary>
    private void RefreshAll()
    {
        RefreshMethodUi();
        RefreshLossesModelUi();
        RefreshVoxelSizeText();
        RefreshAlphaSliders(false);
        RefreshSliderTexts();
        RefreshVoxelCount();
    }

    /// <summary>
    /// Shows the method-specific rows for the selected reconstruction method.
    /// </summary>
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

        // Omni maximum gain only affects the Omni method
        if (omniMaxGainRow != null)
        {
            if (methodDropdown.value == 2)
            {
                omniMaxGainRow.SetActive(true);
            }
            else
            {
                omniMaxGainRow.SetActive(false);
            }
        }
    }

    /// <summary>
    /// Shows the NLOS warning when ABG and NLOS are selected.
    /// </summary>
    private void RefreshEnvironmentUi()
    {
        bool usesAbg = lossesModelDropdown.value == 0;

        if (usesAbg && environmentDropdown.value == 1)
        {
            nlosAlert.SetActive(true);
        }
        else
        {
            nlosAlert.SetActive(false);
        }
    }

    /// <summary>
    /// Shows scenario and environment rows only for ABG losses.
    /// </summary>
    private void RefreshLossesModelUi()
    {
        bool usesAbg = lossesModelDropdown.value == 0;

        scenarioRow.SetActive(usesAbg);
        environmentRow.SetActive(usesAbg);

        RefreshEnvironmentUi();
    }

    /// <summary>
    /// Updates the voxel size text from the selected fixed value.
    /// </summary>
    private void RefreshVoxelSizeText()
    {
        float voxelSize = voxelSizes[currentVoxelSizeIndex];
        voxelSizeValueText.text = FormatFloat(voxelSize, "0.##") + " m";
    }

    /// <summary>
    /// Keeps min alpha lower than max alpha.
    /// </summary>
    private void RefreshAlphaSliders(bool changedMinAlpha)
    {
        float minimumGap = 0.01f;

        float minAlpha = Mathf.Clamp01(minAlphaSlider.value);
        float maxAlpha = Mathf.Clamp01(maxAlphaSlider.value);

        // Keeps min alpha lower than max alpha
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

    /// <summary>
    /// Updates the visible values next to the sliders.
    /// </summary>
    private void RefreshSliderTexts()
    {
        kValueText.text = FormatFloat(kSlider.value, "F2");
        minAlphaValueText.text = FormatFloat(minAlphaSlider.value, "F2");
        maxAlphaValueText.text = FormatFloat(maxAlphaSlider.value, "F2");
        alphaExponentValueText.text = FormatFloat(alphaExponentSlider.value, "F2");
    }

    /// <summary>
    /// Updates the voxel count preview from grid size and voxel size.
    /// </summary>
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

    /// <summary>
    /// Validates every editable input field.
    /// </summary>
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

    /// <summary>
    /// Validates decimal fields from the antenna and propagation panel.
    /// </summary>
    private bool ValidateAntennaPropagationInputs()
    {
        bool allValid = true;
        float value;

        // Tx power can be positive, zero or negative in dBm
        bool txPowerValid = TryReadDecimal(txPowerInput, out value);
        SetInputValid(txPowerInput, txPowerValid);

        if (!txPowerValid)
        {
            allValid = false;
        }

        // Omni maximum gain is only required by the Omni method
        if (methodDropdown.value == 2)
        {
            bool omniGainValid = TryReadDecimal(omniMaxGainInput, out value);
            SetInputValid(omniMaxGainInput, omniGainValid);

            if (!omniGainValid)
            {
                allValid = false;
            }
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

    /// <summary>
    /// Validates grid integer fields and receiver gain decimal fields.
    /// </summary>
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

        // Receiver gains can be positive, zero or negative in dBi
        bool carGainValid = TryReadDecimal(vehicularRxGainInput, out gainValue);
        SetInputValid(vehicularRxGainInput, carGainValid);

        if (!carGainValid)
        {
            allValid = false;
        }

        bool humanGainValid = TryReadDecimal(cellularRxGainInput, out gainValue);
        SetInputValid(cellularRxGainInput, humanGainValid);

        if (!humanGainValid)
        {
            allValid = false;
        }

        return allValid;
    }

    /// <summary>
    /// Reads an integer input using invariant culture.
    /// </summary>
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

    /// <summary>
    /// Reads a decimal input using dot as decimal separator.
    /// </summary>
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

        // The simulator uses English decimal format so commas are not valid
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

    /// <summary>
    /// Sets the input background color according to validation state.
    /// </summary>
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

    /// <summary>
    /// Reads an integer input or returns the default value.
    /// </summary>
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

    /// <summary>
    /// Finds the fixed voxel size index matching the loaded value.
    /// </summary>
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

    /// <summary>
    /// Formats floats using invariant culture.
    /// </summary>
    private string FormatFloat(float value, string format)
    {
        return value.ToString(format, CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Handles reconstruction method dropdown changes.
    /// </summary>
    private void OnMethodChanged(int value)
    {
        RefreshMethodUi();
    }

    /// <summary>
    /// Rounds the K slider value to fixed small steps.
    /// </summary>
    private void OnKSliderChanged(float value)
    {
        float roundedValue = Mathf.Round(value / 0.05f) * 0.05f;

        if (!Mathf.Approximately(kSlider.value, roundedValue))
        {
            kSlider.SetValueWithoutNotify(roundedValue);
        }

        RefreshSliderTexts();
    }

    /// <summary>
    /// Handles min alpha slider changes.
    /// </summary>
    private void OnMinAlphaSliderChanged(float value)
    {
        RefreshAlphaSliders(true);
    }

    /// <summary>
    /// Handles max alpha slider changes.
    /// </summary>
    private void OnMaxAlphaSliderChanged(float value)
    {
        RefreshAlphaSliders(false);
    }

    /// <summary>
    /// Handles alpha exponent slider changes.
    /// </summary>
    private void OnAlphaExponentSliderChanged(float value)
    {
        RefreshSliderTexts();
    }

    /// <summary>
    /// Handles grid input changes.
    /// </summary>
    private void OnGridInputChanged(string value)
    {
        RefreshVoxelCount();
    }

    /// <summary>
    /// Handles environment dropdown changes.
    /// </summary>
    private void OnEnvironmentChanged(int value)
    {
        RefreshEnvironmentUi();
    }

    /// <summary>
    /// Handles losses model dropdown changes.
    /// </summary>
    private void OnLossesModelChanged(int value)
    {
        RefreshLossesModelUi();
    }
}
