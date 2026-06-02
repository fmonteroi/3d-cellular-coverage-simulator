using UnityEngine;

/// <summary>
/// Moves an object through a waypoint path in a loop.
/// </summary>
public class WaypointMover : MonoBehaviour
{
    public WaypointPath path;
    public float moveSpeed = 2f;
    public float rotationSpeed = 8f;
    public float reachDistance = 0.2f;
    public bool loop = true;

    int currentPointIndex = 0;

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

        Vector3 direction = targetPoint.position - transform.position;

        // Keeps the movement on the horizontal plane
        // direction.y = 0f; 

        if (direction.sqrMagnitude <= reachDistance * reachDistance)
        {
            GoToNextPoint();
            return;
        }

        Vector3 moveDirection = direction.normalized;

        transform.position += moveDirection * moveSpeed * Time.deltaTime;

        if (moveDirection.sqrMagnitude > 0.0001f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(moveDirection, Vector3.up);
            transform.rotation = Quaternion.Slerp(
                transform.rotation,
                targetRotation,
                rotationSpeed * Time.deltaTime
            );
        }
    }

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
            }
            else
            {
                currentPointIndex = path.points.Count - 1;
                enabled = false;
            }
        }
    }
}
