using System.Collections.Generic;
using UnityEngine.UI;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Switches between heatmap view, pattern view and mobile receiver views.
/// </summary>
public class SimulationViewManager : MonoBehaviour
{
    public Camera targetCamera;

    [Header("Heatmap view")]
    public Transform heatmapViewCameraPoint;
    public Transform heatmapViewLookPoint;
    public GameObject heatmapViewControlPanel;
    public Slider heatmapViewZoomSlider;
    public Slider heatmapViewRotationSlider;
    public Slider heatmapViewElevationSlider;
    public GameObject mini2DHeatmapPanel;
    public Heatmap2DPanel heatmap2DPanel;

    [Header("Pattern view")]
    public Transform patternViewCameraPoint;
    public Transform patternViewLookPoint;
    public GameObject patternViewPanel;
    public Slider patternViewZoomSlider;
    public Slider patternViewRotationSlider;
    public Slider patternViewElevationSlider;

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
        // Initialize the view to heatmap view at the start
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

        // Do not switch views while the expanded heatmap is open
        if (heatmap2DPanel != null && heatmap2DPanel.IsExpandedViewOpen)
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

        // Goes to heatmap view after the last receiver
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

        // Goes to the last receiver when going left from heatmap view
        if (currentViewIndex < 0)
        {
            currentViewIndex = receivers.Count + 1;
        }

        // Refreshes the UI state after changing the view
        ApplyView();
    }

    private void ApplyView()
    {

        if (heatmapViewControlPanel != null)
        {
            heatmapViewControlPanel.SetActive(false);
        }

        if (patternViewPanel != null)
        {
            patternViewPanel.SetActive(false);
        }

        if (metricsPanel != null)
        {
            metricsPanel.HideMetrics();
        }

        if (mini2DHeatmapPanel != null)
        {
            mini2DHeatmapPanel.SetActive(false);
        }


        if (IsHeatmapView())
        {
            if (cameraText != null)
            {
                cameraText.text = "Heatmap view";
            }

            if (heatmapViewControlPanel != null)
            {
                heatmapViewControlPanel.SetActive(true);
            }

            if (mini2DHeatmapPanel != null)
            {
                mini2DHeatmapPanel.SetActive(true);
            }

            SetSceneViewObjects(showVoxels: true, showPattern: false);
            return;
        }


        if (IsPatternView())
        {
            if (cameraText != null)
            {
                cameraText.text = "Pattern view";
            }

            if (patternViewPanel != null)
            {
                patternViewPanel.SetActive(true);
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
        if (!TreyGetViewTarget(out Vector3 desiredPosition, out Vector3 desiredLookPosition))
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

    private bool TreyGetViewTarget(out Vector3 desiredPosition, out Vector3 desiredLookPosition)
    {
        // Initialize out parameters with safe defaults
        desiredPosition = Vector3.zero;
        desiredLookPosition = Vector3.zero;

        if (IsHeatmapView())
        {
            return TryCalculateCameraTransform(heatmapViewCameraPoint, heatmapViewLookPoint, heatmapViewZoomSlider, heatmapViewRotationSlider, heatmapViewElevationSlider, out desiredPosition, out desiredLookPosition);
        }

        if (IsPatternView())
        {
            return TryCalculateCameraTransform(patternViewCameraPoint, patternViewLookPoint, patternViewZoomSlider, patternViewRotationSlider, patternViewElevationSlider, out desiredPosition, out desiredLookPosition);
        }

        // Receiver view follows the currently selected receiver
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

    private bool TryCalculateCameraTransform(Transform cameraPoint, Transform lookPoint, Slider zoomSlider, Slider rotationSlider,
                                        Slider elevationSlider, out Vector3 desiredPosition, out Vector3 desiredLookPosition)
    {
        desiredPosition = Vector3.zero;
        desiredLookPosition = Vector3.zero;

        if (cameraPoint == null || lookPoint == null)
        {
            return false;
        }

        desiredLookPosition = lookPoint.position;

        // Original direction and distance from the target to the camera
        Vector3 originalDirection = cameraPoint.position - lookPoint.position;

        if (originalDirection.sqrMagnitude <= 0.001f)
        {
            return false;
        }

        // Slider to the right means closer camera
        float zoomMultiplier = 1f;

        if (zoomSlider != null)
        {
            zoomMultiplier = zoomSlider.maxValue + zoomSlider.minValue - zoomSlider.value;
        }

        // Read the horizontal rotation
        float horizontalDegrees = 0f;

        if (rotationSlider != null)
        {
            horizontalDegrees = rotationSlider.value;
        }

        Quaternion horizontalRotation = Quaternion.AngleAxis(horizontalDegrees, Vector3.up);

        Vector3 horizontalDirection = horizontalRotation * originalDirection.normalized;

        // Read the vertical rotation
        float elevationDegrees = 0f;

        if (elevationSlider != null)
        {
            elevationDegrees = -elevationSlider.value;
        }

        Vector3 elevationAxis = Vector3.Cross(Vector3.up, horizontalDirection).normalized;

        Quaternion elevationRotation = Quaternion.AngleAxis(elevationDegrees, elevationAxis);

        Vector3 finalDirection = elevationRotation * horizontalDirection;

        float finalDistance = originalDirection.magnitude * zoomMultiplier;

        desiredPosition = lookPoint.position + finalDirection * finalDistance;

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

    private bool IsHeatmapView()
    {
        return currentViewIndex == 0;
    }

    private bool IsPatternView()
    {
        return currentViewIndex == 1;
    }

    private bool IsReceiverView()
    {
        return currentViewIndex >= 2;
    }

}
