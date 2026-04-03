using System;
using UnityEngine;

/// <summary>
/// Stores metrics of a mobile receiver.
/// </summary>
[Serializable]
public class ReceiverMetricsSnapshot
{
    public float timeSeconds;
    public Vector3 worldPosition;

    public float txPowerDbm;
    public float txGainDbi;
    public float rxGainDbi;

    public float distanceMeters;
    public int buildingCollisions;
    public float buildingLossDb;

    public float basePathLossDb;
    public float pathLossDb;
    public float prxDbm;
    public float snrDb;
    public float propagationLatencyMs;
}
