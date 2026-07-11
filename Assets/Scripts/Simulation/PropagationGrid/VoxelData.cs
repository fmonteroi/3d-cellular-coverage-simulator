using System;
using UnityEngine;

/// <summary>
/// Stores the data of one simulated voxel.
/// </summary>
[Serializable]
public class VoxelData
{
    [Header("Grid index")]
    public int index;
    public int gridX;
    public int gridY;
    public int gridZ;

    [Header("Geometry")]
    public Vector3 centerWorldPosition;
    public float distanceMeters;
    public int buildingCollisions;

    [Header("Link budget values")]
    public float txPowerDbm;
    public float txGainDbi;
    public float rxGainDbi;
    public float pathLossDb;

    [Header("Final result")]
    public float prxDbm;
}
