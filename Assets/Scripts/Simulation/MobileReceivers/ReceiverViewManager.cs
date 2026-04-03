using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Switches between overview mode and mobile receiver views.
/// </summary>
public class ReceiverViewManager : MonoBehaviour
{
    public Camera targetCamera;

    [Header("Overview")]
    public Transform overviewCameraPoint;
    public Transform overviewLookPoint;

    [Header("Receivers")]
    public List<MobileReceiverMetrics> receivers = new List<MobileReceiverMetrics>();

    [Header("Movement")]
    public float cameraMoveSpeed = 2f;
    public float cameraLookSpeed = 2f;

    [Header("UI")]
    public ReceiverMetricsPanel metricsPanel;

    int currentViewIndex = 0;

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
        if (currentViewIndex > receivers.Count)
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
            currentViewIndex = receivers.Count;
        }

        // Refreshes the UI state after changing the view
        ApplyView();
    }

    private void ApplyView()
    {
        if (metricsPanel == null)
        {
            return;
        }

        // In overview mode the metrics panel must stay hidden
        if (IsOverviewMode())
        {
            metricsPanel.ShowOverview();
            return;
        }

        // Gets the receiver associated with the active view index
        MobileReceiverMetrics receiver = GetCurrentReceiver();

        if (receiver == null)
        {
            metricsPanel.ShowOverview();
            return;
        }

        metricsPanel.ShowReceiver(receiver);
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

            desiredPosition = overviewCameraPoint.position;
            desiredLookPosition = overviewLookPoint.position;
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

    private bool IsOverviewMode()
    {
        // Index 0 is the overview camera
        return currentViewIndex == 0;
    }

    private MobileReceiverMetrics GetCurrentReceiver()
    {
        // Overview mode has no active receiver
        if (currentViewIndex <= 0)
        {
            return null;
        }

        // Convert the view index into the receiver list index
        int receiverIndex = currentViewIndex - 1;

        // Guard against invalid indices
        if (receiverIndex < 0 || receiverIndex >= receivers.Count)
        {
            return null;
        }

        // Returns the current receiver
        return receivers[receiverIndex];
    }
}
