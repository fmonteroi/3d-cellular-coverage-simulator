using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Stores the shared propagation settings.
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
    [Min(0.001f)] public float minimumDistanceMeters = 1f;
    [Min(0.001f)] public float bandwidthMHz = 10f;


    [Header("Propagation channel")]
    public ScenarioType scenario = ScenarioType.Umi;
    public EnvironmentType environmentType = EnvironmentType.LOS;
    public LossesModelType lossesModel = LossesModelType.ABG;
    public bool disableShadowing = true;


    [Header("Building losses")]
    public LayerMask buildingLayerMask;
    [Min(0f)] public float lossPerBuildingDb = 3f;

    [Header("Debug")]
    public bool showDebug = false;

    public bool ValidateSetup()
    {
        // Validate transmitter reference
        if (transmitter == null)
        {
            Debug.LogError("PropagationSettings: Transmitter is not assigned.");
            return false;
        }

        // Validate gain reconstruction reference
        if (patternReconstructor == null)
        {
            Debug.LogError("PropagationSettings: PatternGainReconstructor is not assigned.");
            return false;
        }

        // Validate gain matrix availability
        if (!patternReconstructor.IsReady)
        {
            Debug.LogError("PropagationSettings: PatternGainReconstructor is not ready.");
            return false;
        }
        if (showDebug)
        {
            Debug.Log($"Ganancia en 90,90={patternReconstructor.GetGainDbi(90, 90)} dBi");
            Debug.Log($"Ganancia en 90,0={patternReconstructor.GetGainDbi(90, 0)} dBi");
            Debug.Log($"Ganancia en 90,270={patternReconstructor.GetGainDbi(90, 270)} dBi");
        }

        return true;
    }

    public float EvaluateTxGainDbi(Vector3 rxWorldPosition, string debugLabel = "")
    {
        // Direction from transmiter to receiver
        Vector3 worldDirection = rxWorldPosition - transmitter.position;

        // If the receiver is exactly at the transmitter position, return the max gain
        if (worldDirection.sqrMagnitude <= 0.001f)
        {
            return patternReconstructor.MaxGainDbi;
        }

        // Converts the direction to local antenna coordinates
        Vector3 localDirection = transmitter.InverseTransformDirection(worldDirection.normalized).normalized;

        // Gets theta from the local direction
        int theta = Mathf.RoundToInt(Mathf.Acos(Mathf.Clamp(localDirection.y, -1f, 1f)) * Mathf.Rad2Deg);

        // Gets phi from the local direction
        int phi = Mathf.RoundToInt(Mathf.Atan2(localDirection.x, localDirection.z) * Mathf.Rad2Deg);
        if (phi < 0)
        {
            phi += 360;
        }

        // Read the absolute gain from the matrix
        float gainDbi = patternReconstructor.GetGainDbi(theta, phi);

        // Debug if enabled
        if (showDebug)
        {
            Debug.Log($"{debugLabel} Theta={theta} Phi={phi} Gain={gainDbi} dBi");
        }


        // Read the absolute gain from the matrix
        return gainDbi;
    }



    public int CountBuildingCollisions(Vector3 rxWorldPosition)
    {
        // If no building layer is selected, no building loss is applied
        if (buildingLayerMask.value == 0)
        {
            return 0;
        }

        // Direction from transmiter to receiver
        Vector3 worldDirection = rxWorldPosition - transmitter.position;

        // If the receiver is exactly at the transmitter position, return zero buildings
        if (worldDirection.sqrMagnitude <= 0.001f)
        {
            return 0;
        }

        // Cast along the TX -> RX direction and collect all crossed building colliders
        RaycastHit[] hits = Physics.RaycastAll(
            transmitter.position,
            worldDirection.normalized,
            worldDirection.magnitude,
            buildingLayerMask,
            QueryTriggerInteraction.Ignore);

        // Count unique colliders to avoid duplicated hits
        HashSet<Collider> crossedBuildings = new HashSet<Collider>();

        for (int i = 0; i < hits.Length; i++)
        {
            crossedBuildings.Add(hits[i].collider);
        }

        return crossedBuildings.Count;
    }

    public BridgeRequestDto BuildBaseRequest()
    {
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
}
