using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Stores a list of waypoint transforms for a moving receiver.
/// </summary>
public class WaypointPath : MonoBehaviour
{
    public List<Transform> points = new List<Transform>();

    void OnDrawGizmos()
    {
        if (points == null || points.Count < 2)
        {
            return;
        }

        Gizmos.color = Color.cyan;

        for (int i = 0; i < points.Count; i++)
        {
            if (points[i] == null)
            {
                continue;
            }

            Gizmos.DrawSphere(points[i].position, 0.3f);

            Transform next = points[(i + 1) % points.Count];
            if (next != null)
            {
                Gizmos.DrawLine(points[i].position, next.position);
            }
        }
    }
}
