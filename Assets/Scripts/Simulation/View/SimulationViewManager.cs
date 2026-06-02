using System.Collections.Generic;
using UnityEngine.UI;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Switches between overview mode and mobile receiver views.
/// </summary>
public class SimulationViewManager : MonoBehaviour
{
    public Camera targetCamera;

    [Header("Overview")]
    public Transform overviewCameraPoint;
    public Transform overviewLookPoint;

    [Header("Overview controls")]
    public GameObject overviewControlsPanel;
    public Slider overviewZoomSlider;
    public Slider overviewRotationSlider;

    [Header("Radiation pattern")]
    public Transform radiationPatternCameraPoint;
    public Transform radiationPatternLookPoint;

    [Header("Scene visibility")]
    public GameObject prxVoxelRenderer;
    public MeshRenderer patternMeshRenderer;

    [Header("Camera UI")]
    public TMP_Text cameraText;

    [Header("Receivers")]
    public List<MobileReceiverMetrics> receivers = new List<MobileReceiverMetrics>();

    [Header("Movement")]
    public float cameraMoveSpeed = 2f;
    public float cameraLookSpeed = 2f;

    [Header("UI")]
    public ReceiverMetricsPanel metricsPanel;

    private int currentViewIndex = 0;

    void Start()
    {
        // Initialize the view to overview mode at the start
        ApplyView();
    }

    void Update()
    {
        // Handles user input for switching views and update the camera position and orientation
        HandleInput();

        // Smoothly moves the camera towards the active target
        UpdateCamera();
    }

    private void HandleInput()
    {
        // Do not switch views while the simulation is paused
        if (Time.timeScale == 0f)
        {
            return;
        }

        // Reads the current keyboard state from the Input System
        Keyboard keyboard = Keyboard.current;

        if (keyboard == null)
        {
            return;
        }

        // Moves to the next available view
        if (keyboard.rightArrowKey.wasPressedThisFrame || keyboard.dKey.wasPressedThisFrame)
        {
            MoveToNextView();
        }

        // Moves to the previous available view
        if (keyboard.leftArrowKey.wasPressedThisFrame || keyboard.aKey.wasPressedThisFrame)
        {
            MoveToPreviousView();
        }
    }

    private void MoveToNextView()
    {
        currentViewIndex++;

        // Goes to overview after the last receiver
        if (currentViewIndex >= receivers.Count + 2)
        {
            currentViewIndex = 0;
        }

        // Refreshes the UI state after changing the view
        ApplyView();
    }

    private void MoveToPreviousView()
    {
        currentViewIndex--;

        // Goes to the last receiver when going left from overview
        if (currentViewIndex < 0)
        {
            currentViewIndex = receivers.Count + 1;
        }

        // Refreshes the UI state after changing the view
        ApplyView();
    }

    private void ApplyView()
    {
        if (IsOverviewMode())
        {
            if (cameraText != null)
            {
                cameraText.text = "Overview";
            }

            if (overviewControlsPanel != null)
            {
                overviewControlsPanel.SetActive(true);
            }

            if (metricsPanel != null)
            {
                metricsPanel.HideMetrics();
            }

            SetSceneViewObjects(showVoxels: true, showPattern: false);
            return;
        }

        if (overviewControlsPanel != null)
        {
            overviewControlsPanel.SetActive(false);
        }


        if (IsRadiationPatternMode())
        {
            if (cameraText != null)
            {
                cameraText.text = "Radiation pattern";
            }

            if (metricsPanel != null)
            {
                metricsPanel.HideMetrics();
            }

            SetSceneViewObjects(showVoxels: false, showPattern: true);
            return;
        }

        MobileReceiverMetrics receiver = GetCurrentReceiver();

        if (receiver == null)
        {
            return;
        }

        if (cameraText != null)
        {
            cameraText.text = $"Metrics {receiver.receiverId}";
        }

        if (metricsPanel != null)
        {
            metricsPanel.ShowMetrics(receiver);
        }

        SetSceneViewObjects(showVoxels: false, showPattern: false);
    }

    private void UpdateCamera()
    {
        // No camera movement is possible without a target camera
        if (targetCamera == null)
        {
            return;
        }

        // Resolve the desired camera position and look point for the current view
        if (!TryGetCameraTargets(out Vector3 desiredPosition, out Vector3 desiredLookPosition))
        {
            return;
        }

        // Smoothly move the camera towards the desired position
        targetCamera.transform.position = Vector3.Lerp(
            targetCamera.transform.position,
            desiredPosition,
            cameraMoveSpeed * Time.deltaTime
        );

        // Build the desired rotation so the camera looks at the active target
        Quaternion targetRotation = Quaternion.LookRotation(
            desiredLookPosition - targetCamera.transform.position,
            Vector3.up
        );

        // Smoothly rotate the camera towards the desired orientation
        targetCamera.transform.rotation = Quaternion.Slerp(
            targetCamera.transform.rotation,
            targetRotation,
            cameraLookSpeed * Time.deltaTime
        );
    }

    private bool TryGetCameraTargets(out Vector3 desiredPosition, out Vector3 desiredLookPosition)
    {
        // Initialize out parameters with safe defaults
        desiredPosition = Vector3.zero;
        desiredLookPosition = Vector3.zero;

        if (IsOverviewMode())
        {
            // Overview mode uses fixed scene anchors for camera and look targets
            if (overviewCameraPoint == null || overviewLookPoint == null)
            {
                return false;
            }

            desiredLookPosition = overviewLookPoint.position;

            Vector3 overviewDirection = overviewCameraPoint.position - overviewLookPoint.position;

            float zoomMultiplier = 1f;

            if (overviewZoomSlider != null)
            {
                // Slider to the right means closer camera
                zoomMultiplier = overviewZoomSlider.maxValue + overviewZoomSlider.minValue - overviewZoomSlider.value;
            }

            float rotationDegrees = 0f;

            if (overviewRotationSlider != null)
            {
                rotationDegrees = overviewRotationSlider.value;
            }

            Quaternion orbitRotation = Quaternion.AngleAxis(rotationDegrees, Vector3.up);

            Vector3 rotatedDirection = orbitRotation * overviewDirection.normalized;
            float overviewDistance = overviewDirection.magnitude * zoomMultiplier;

            desiredPosition = overviewLookPoint.position + rotatedDirection * overviewDistance;
            return true;
        }

        if (IsRadiationPatternMode())
        {
            // Radiation pattern mode uses fixed scene anchors for camera and look targets
            if (radiationPatternCameraPoint == null || radiationPatternLookPoint == null)
            {
                return false;
            }

            desiredPosition = radiationPatternCameraPoint.position;
            desiredLookPosition = radiationPatternLookPoint.position;
            return true;
        }

        // Receiver mode follows the currently selected receiver
        MobileReceiverMetrics receiver = GetCurrentReceiver();

        if (receiver == null)
        {
            return false;
        }

        // Each receiver provides its own camera offsets through ReceiverViewTarget
        ReceiverViewTarget viewTarget = receiver.GetComponent<ReceiverViewTarget>();

        if (viewTarget == null)
        {
            return false;
        }

        // Read the camera follow position and look point from the receiver
        desiredPosition = viewTarget.GetCameraPosition();
        desiredLookPosition = viewTarget.GetLookPosition();
        return true;
    }


    private MobileReceiverMetrics GetCurrentReceiver()
    {
        // Convert the view index into the receiver list index
        int receiverIndex = currentViewIndex - 2;

        // Guard against invalid indices
        if (receiverIndex < 0 || receiverIndex >= receivers.Count)
        {
            return null;
        }

        // Returns the current receiver
        return receivers[receiverIndex];
    }

    private void SetSceneViewObjects(bool showVoxels, bool showPattern)
    {
        if (prxVoxelRenderer != null)
        {
            prxVoxelRenderer.SetActive(showVoxels);
        }

        if (patternMeshRenderer != null)
        {
            patternMeshRenderer.enabled = showPattern;
        }
    }

    private bool IsOverviewMode()
    {
        return currentViewIndex == 0;
    }

    private bool IsRadiationPatternMode()
    {
        return currentViewIndex == 1;
    }

    private bool IsReceiverMode()
    {
        return currentViewIndex >= 2;
    }

}
