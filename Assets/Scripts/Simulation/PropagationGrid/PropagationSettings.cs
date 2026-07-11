using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Stores shared propagation settings and evaluates antenna gain and building losses.
/// </summary>
public class PropagationSettings : MonoBehaviour
{
    // --------------------------------------------------
    // Channel options
    // --------------------------------------------------

    public enum ScenarioType
    {
        Umi,
        UMa,
        Indoor
    }

    public enum EnvironmentType
    {
        LOS,
        NLOS
    }

    public enum LossesModelType
    {
        ABG,
        FSPL
    }

    // --------------------------------------------------
    // Input parameters
    // --------------------------------------------------

    [Header("References")]
    public PatternGainReconstructor patternReconstructor;
    public Transform transmitter;

    [Header("Link budget")]
    public float txPowerDbm = 30f;
    public float rxGainDbi = 0f;
    public float frequencyGHz = 1.785f;
    [Min(0.001f)] public float minimumDistanceMeters = 0.001f;
    [Min(0.001f)] public float bandwidthMHz = 10f;


    [Header("Propagation channel")]
    public ScenarioType scenario = ScenarioType.Umi;
    public EnvironmentType environmentType = EnvironmentType.LOS;
    public LossesModelType lossesModel = LossesModelType.ABG;
    public bool disableShadowing = true;


    [Header("Building losses")]
    public LayerMask buildingLayerMask;

    [Header("Debug")]
    public bool showDebug = false;

    /// <summary>
    /// Checks that the references required for propagation calculations are ready.
    /// </summary>
    public bool ValidateSetup()
    {
        // Checks the transmitter reference
        if (transmitter == null)
        {
            Debug.LogError("PropagationSettings: Transmitter is not assigned.");
            return false;
        }

        // Checks the gain reconstructor reference
        if (patternReconstructor == null)
        {
            Debug.LogError("PropagationSettings: PatternGainReconstructor is not assigned.");
            return false;
        }

        // Checks that the gain matrix is ready
        if (!patternReconstructor.IsReady)
        {
            Debug.LogError("PropagationSettings: PatternGainReconstructor is not ready.");
            return false;
        }
        if (showDebug)
        {
            LogTest(90, 0, "16.48 dBi");
            LogTest(90, 90, "2.53 dBi");
            LogTest(90, 180, "-18.82 dBi");
            LogTest(90, 230, "-12.84 dBi");
            LogTest(90, 270, "0.92 dBi");

            LogTest(180, 0, "-18.30 dBi");
            LogTest(0, 0, "-15.45 dBi");

            // Test angle used during the Matlab comparison
            LogTest(0, 185, "-35.62 dBi");
        }

        return true;
    }

    /// <summary>
    /// Calculates the transmitter antenna gain towards a receiver world position.
    /// </summary>
    public float EvaluateTxGainDbi(Vector3 rxWorldPosition, string debugLabel = "")
    {
        // Gets the direction from the transmitter to the receiver
        Vector3 worldDirection = rxWorldPosition - transmitter.position;

        // Returns the maximum gain when both positions are equal
        if (worldDirection.sqrMagnitude <= 0.001f)
        {
            return patternReconstructor.MaxGainDbi;
        }

        // Converts the direction to local antenna coordinates
        Vector3 localDirection = transmitter.InverseTransformDirection(worldDirection.normalized).normalized;

        // Calculates theta from the local direction
        int theta = Mathf.RoundToInt(Mathf.Acos(Mathf.Clamp(localDirection.y, -1f, 1f)) * Mathf.Rad2Deg);

        // Calculates phi from the local direction
        int phi = Mathf.RoundToInt(Mathf.Atan2(localDirection.x, localDirection.z) * Mathf.Rad2Deg);
        if (phi < 0)
        {
            phi += 360;
        }

        // Reads the absolute gain from the matrix
        float gainDbi = patternReconstructor.GetGainDbi(theta, phi);

        // Prints the calculated angles and gain when debug is enabled
        if (showDebug)
        {
            Debug.Log($"{debugLabel} Theta={theta} Phi={phi} Gain={gainDbi} dBi");
        }

        return gainDbi;
    }

    /// <summary>
    /// Counts the building wall crossings between the transmitter and one receiver position.
    /// </summary>
    public int CountBuildingCollisions(Vector3 rxWorldPosition)
    {
        // Skips collision checks when no building layer is selected
        if (buildingLayerMask.value == 0)
        {
            return 0;
        }

        // Builds the segment from the transmitter to the receiver
        Vector3 startPosition = transmitter.position;
        Vector3 worldDirection = rxWorldPosition - startPosition;

        // Skips an empty segment
        if (worldDirection.sqrMagnitude <= 0.001f)
        {
            return 0;
        }

        float segmentLength = worldDirection.magnitude;
        Vector3 direction = worldDirection.normalized;

        // Finds every building piece crossed by the segment
        RaycastHit[] hits = Physics.RaycastAll(
            startPosition,
            direction,
            segmentLength,
            buildingLayerMask,
            QueryTriggerInteraction.Ignore
        );

        // Stores processed colliders and their occupied intervals
        HashSet<Collider> checkedColliders = new HashSet<Collider>();
        List<Vector2> intervals = new List<Vector2>();

        for (int i = 0; i < hits.Length; i++)
        {
            Collider currentCollider = hits[i].collider;

            // Processes each collider only once
            if (checkedColliders.Contains(currentCollider))
            {
                continue;
            }

            checkedColliders.Add(currentCollider);

            AddColliderInterval(currentCollider, startPosition, rxWorldPosition, direction, segmentLength, intervals);
        }

        // Merges connected pieces and counts the crossed walls
        return CountWallCrossings(intervals, segmentLength);
    }

    /// <summary>
    /// Adds the occupied interval of one collider along the transmitter receiver segment.
    /// </summary>
    private void AddColliderInterval(Collider buildingCollider, Vector3 startPosition, Vector3 endPosition, Vector3 direction, float segmentLength, List<Vector2> intervals)
    {
        // Casts from both ends to find the entry and exit points
        Ray forwardRay = new Ray(startPosition, direction);
        Ray backwardRay = new Ray(endPosition, -direction);

        RaycastHit entryHit;
        RaycastHit exitHit;

        bool foundEntry = buildingCollider.Raycast(forwardRay, out entryHit, segmentLength);
        bool foundExit = buildingCollider.Raycast(backwardRay, out exitHit, segmentLength);

        // Requires the forward ray to find the collider
        if (!foundEntry)
        {
            return;
        }

        float entryDistance = entryHit.distance;
        float exitDistance;

        if (foundExit)
        {
            // Converts the exit distance to use the transmitter as origin
            exitDistance = segmentLength - exitHit.distance;
        }
        else
        {
            // The backward ray starts inside the collider
            // The occupied interval finishes at the receiver
            exitDistance = segmentLength;
        }

        // Keeps the interval ordered from start to end
        if (entryDistance > exitDistance)
        {
            float temporary = entryDistance;
            entryDistance = exitDistance;
            exitDistance = temporary;
        }

        const float minimumThickness = 0.01f;

        // Ignores contacts that only touch an edge or corner
        if (exitDistance - entryDistance <= minimumThickness)
        {
            return;
        }

        // Stores entry in x and exit in y
        intervals.Add(new Vector2(entryDistance, exitDistance));
    }

    /// <summary>
    /// Merges collider intervals and converts continuous sections into wall crossings.
    /// </summary>
    private int CountWallCrossings(List<Vector2> intervals, float segmentLength)
    {
        // No intervals means no crossed walls
        if (intervals.Count == 0)
        {
            return 0;
        }

        // Sorts intervals by their entry distance
        intervals.Sort(
            delegate (Vector2 first, Vector2 second)
            {
                return first.x.CompareTo(second.x);
            }
        );

        const float tolerance = 0.01f;

        int continuousSections = 1;
        float currentEnd = intervals[0].y;

        for (int i = 1; i < intervals.Count; i++)
        {
            Vector2 nextInterval = intervals[i];

            // Merges intervals that overlap or touch
            if (nextInterval.x <= currentEnd + tolerance)
            {
                currentEnd = Mathf.Max(currentEnd, nextInterval.y);
            }
            else
            {
                continuousSections++;
                currentEnd = nextInterval.y;
            }
        }

        // Counts one entry and one exit wall per continuous section
        int wallCrossings = continuousSections * 2;

        // Removes the exit wall when the receiver finishes inside
        if (currentEnd >= segmentLength - tolerance)
        {
            wallCrossings--;
        }

        return wallCrossings;
    }

    /// <summary>
    /// Builds the common bridge request fields from the current propagation settings.
    /// </summary>
    public BridgeRequestDto BuildBaseRequest()
    {
        // Copies the shared settings into the bridge request
        return new BridgeRequestDto
        {
            scenario = scenario.ToString(),
            environmentType = environmentType.ToString(),
            lossesModel = lossesModel.ToString(),
            frequencyGHz = frequencyGHz,
            txPowerDbm = txPowerDbm,
            rxGainDbi = rxGainDbi,
            minimumDistanceMeters = minimumDistanceMeters,
            bandwidthMHz = bandwidthMHz,
            disableShadowing = disableShadowing,
            transmitterX = transmitter.position.x,
            transmitterY = transmitter.position.y,
            transmitterZ = transmitter.position.z
        };
    }

    /// <summary>
    /// Prints one gain comparison value used during pattern debugging.
    /// </summary>
    private void LogTest(int theta, int phi, string expected)
    {
        float relativeDb = patternReconstructor.GetGainDbRelative(theta, phi);
        float absoluteDbi = patternReconstructor.GetGainDbi(theta, phi);

        Debug.Log(
            $"Angle (theta={theta} phi={phi}) " +
            $"relative={relativeDb:F2} dB absolute={absoluteDbi:F2} dBi | Matlab expected: {expected}"
        );
    }

    /// <summary>
    /// Gets the fixed additional loss applied per crossed wall.
    /// </summary>
    public float GetLossPerWallDb()
    {
        return 5f + 4f * frequencyGHz;
    }
}
