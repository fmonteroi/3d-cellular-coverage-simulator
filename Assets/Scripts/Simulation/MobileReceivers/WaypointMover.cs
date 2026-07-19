using UnityEngine;
using System;

/// <summary>
/// Moves an object through a waypoint path.
/// </summary>
public class WaypointMover : MonoBehaviour
{

    [Header("Path Settings")]
    public WaypointPath path;
    public float moveSpeed = 2f;
    public float rotationSpeed = 4f;
    public float reachDistance = 0.20f;
    public bool loop = true;

    [Header("Results")]
    public bool FirstLapCompleted { get; private set; }
    public event Action<WaypointMover> OnFirstLapCompleted;
    private bool returningToFirstPoint = false;

    int currentPointIndex = 0;

    /// <summary>
    /// Moves the object towards the current waypoint.
    /// </summary>
    void Update()
    {
        if (path == null || path.points == null || path.points.Count == 0)
        {
            return;
        }

        Transform targetPoint = path.points[currentPointIndex];

        if (targetPoint == null)
        {
            return;
        }

        // Stores the position before moving to calculate the real movement direction
        Vector3 previousPosition = transform.position;

        // Moves towards the waypoint without overshooting it
        transform.position = Vector3.MoveTowards(transform.position, targetPoint.position, moveSpeed * Time.deltaTime);

        // Uses the real displacement of this frame as movement direction
        Vector3 moveDirection = transform.position - previousPosition;

        if (moveDirection.sqrMagnitude > 0.0001f)
        {
            // Rotates the object towards its current movement direction
            Quaternion targetRotation = Quaternion.LookRotation(moveDirection.normalized, Vector3.up);

            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
        }

        // Checks arrival after moving so the object does not stop for one frame
        if (Vector3.Distance(transform.position, targetPoint.position) <= reachDistance)
        {
            // Completes a looping route after returning to its first point
            if (loop && returningToFirstPoint && currentPointIndex == 0)
            {
                CompleteFirstLap();
            }

            // Completes a linear route after reaching its last point
            if (!loop && currentPointIndex == path.points.Count - 1)
            {
                CompleteFirstLap();
            }

            GoToNextPoint();
        }
    }

    /// <summary>
    /// Advances to the next waypoint and handles route looping.
    /// </summary>
    private void GoToNextPoint()
    {
        if (path.points.Count == 0)
        {
            return;
        }

        currentPointIndex++;

        if (currentPointIndex >= path.points.Count)
        {
            if (loop)
            {
                currentPointIndex = 0;
                returningToFirstPoint = true;
            }
            else
            {
                currentPointIndex = path.points.Count - 1;
                enabled = false;
            }
        }
    }

    /// <summary>
    /// Marks the route as completed and notifies listeners.
    /// </summary>
    private void CompleteFirstLap()
    {
        if (FirstLapCompleted)
        {
            return;
        }

        FirstLapCompleted = true;

        if (OnFirstLapCompleted != null)
        {
            OnFirstLapCompleted(this);
        }
    }
}
