using System;
using System.Collections.Generic;

/// <summary>
/// Request sent by Unity to the Python bridge.
/// </summary>
[Serializable]
public class BridgeRequestDto
{
    public string requestType;

    public string scenario;
    public string environmentType;
    public string lossesModel;
    public float frequencyGHz;
    public float txPowerDbm;
    public float rxGainDbi;
    public float minimumDistanceMeters;
    public float bandwidthMHz;
    public bool disableShadowing;
    public float transmitterX;
    public float transmitterY;
    public float transmitterZ;

    public List<GridVoxelRequestDto> voxels;
    public List<MobileReceiverRequestDto> receivers;
}

/// <summary>
/// Input data for one grid voxel request.
/// </summary>
[Serializable]
public class GridVoxelRequestDto
{
    public int index;
    public float x;
    public float y;
    public float z;
    public float txGainDbi;
    public int buildingCollisions;
    public float buildingLossDb;
}

/// <summary>
/// Input data for one mobile receiver request.
/// </summary>
[Serializable]
public class MobileReceiverRequestDto
{
    public string id;
    public float x;
    public float y;
    public float z;
    public float txGainDbi;
    public float rxGainDbi;
    public int buildingCollisions;
    public float buildingLossDb;
}

/// <summary>
/// Response returned by the Python bridge.
/// </summary>
[Serializable]
public class BridgeResponseDto
{
    public string error;
    public List<VoxelResultDto> results;
    public List<MobileReceiverResultDto> receiverResults;
}

/// <summary>
/// Result data returned for one grid voxel.
/// </summary>
[Serializable]
public class VoxelResultDto
{
    public int index;
    public int buildingCollisions;
    public float buildingLossDb;
    public float distanceMeters;
    public float pathLossDb;
    public float prxDbm;
}

/// <summary>
/// Result data returned for one mobile receiver.
/// </summary>
[Serializable]
public class MobileReceiverResultDto
{
    public string id;
    public float txGainDbi;
    public int buildingCollisions;
    public float buildingLossDb;
    public float distanceMeters;
    public float basePathLossDb;
    public float pathLossDb;
    public float prxDbm;
    public float snrDb;
}
