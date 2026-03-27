using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using Debug = UnityEngine.Debug;

/// <summary>
/// Builds a 3D receiver grid, launches the Python bridge
/// and stores the received power of each cell.
/// </summary>
[DefaultExecutionOrder(-900)] // Runs after PatternGainReconstructor
public class PropagationGridSimulator : MonoBehaviour
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
    public Transform receiversParent;

    [Header("Grid")]
    public Vector3Int gridSizeMeters = new Vector3Int(10, 10, 10);
    [Min(0.1f)] public float cellSizeMeters = 1f;

    [Header("Link budget")]
    public float txPowerDbm = 30f;
    public float rxGainDbi = 0f;
    public float frequencyGHz = 1.785f;
    [Min(0.001f)] public float minimumDistanceMeters = 1f;

    [Header("Propagation channel")]
    public ScenarioType scenario = ScenarioType.Umi;
    public EnvironmentType environmentType = EnvironmentType.LOS;
    public LossesModelType lossesModel = LossesModelType.ABG;
    public bool disableShadowing = true;

    [Header("Building losses")]
    public LayerMask buildingLayerMask;
    [Min(0f)] public float lossPerBuildingDb = 10f;

    [Header("Python")]
    public string pythonExecutablePath = @"PythonRuntime/python.exe";
    public string pythonServerScriptPath = @"SimulatorBridge/unity_bridge_server.py";
    public string simulatorRootPath = @"SIMULATOR";
    [Min(100)] public int pythonStartupDelayMs = 1000;

    [Header("Debug")]
    public GameObject receiverDebugPrefab;

    // Ready flag
    public bool ResultsReady { get; private set; }

    // Generated debug receivers
    List<VoxelReceiver> receivers;

    // Generated voxel data
    public List<VoxelData> voxelsData;

    // Python process
    Process pythonProcess;

    void Start()
    {
        ResultsReady = false;

        // Use the singleton if no reconstructor was assigned
        if (patternReconstructor == null)
        {
            patternReconstructor = PatternGainReconstructor.Instance;
        }

        // Stop if setup is invalid
        if (!ValidateSetup())
        {
            return;
        }

        // Create a parent object if needed
        EnsureParentExists();

        // Build the full grid and prepare the request data
        RequestPayloadDto payload = BuildGridAndPayload();

        // Reserve a free local TCP port
        int port = GetFreePort();

        try
        {
            // Launch the Python bridge
            StartPythonServer(port);

            Debug.Log("PropagationGridSimulator: Waiting for Python to start...");

            // Give Python time to start the local server
            Thread.Sleep(pythonStartupDelayMs);

            Debug.Log("PropagationGridSimulator: Sending request to Python and waiting for results...");

            // Send the request and wait for the response
            ResponsePayloadDto response = SendRequest(port, payload);

            Debug.Log("PropagationGridSimulator: Received response from Python, applying results...");

            // Stop if Python returned an error
            if (!string.IsNullOrEmpty(response.error))
            {
                Debug.LogError($"PropagationGridSimulator: Python error: {response.error}");
                return;
            }

            // Copy the received values into Unity receivers
            ApplyResponse(response);

            ResultsReady = true;
            Debug.Log("PropagationGridSimulator: voxel grid simulation finished.");

            // Build the voxel visualization if a renderer exists in the scene
            PrxVoxelChunkRenderer renderer = FindFirstObjectByType<PrxVoxelChunkRenderer>();

            if (renderer != null)
            {
                renderer.BuildChunks();
            }
            else
            {
                Debug.LogWarning("PropagationGridSimulator: No PrxVoxelChunkRenderer found in the scene.");
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"PropagationGridSimulator: {ex.Message}");
        }
        finally
        {
            // Always close Python at the end
            ShutdownPython();
        }
    }

    void OnDestroy()
    {
        // Ensure Python is closed if the object is destroyed
        ShutdownPython();
    }

    void OnValidate()
    {
        gridSizeMeters.x = Mathf.Clamp(gridSizeMeters.x, 1, 200);
        gridSizeMeters.y = Mathf.Clamp(gridSizeMeters.y, 1, 200);
        gridSizeMeters.z = Mathf.Clamp(gridSizeMeters.z, 1, 200);
    }

    // --------------------------------------------------
    // Validation
    // --------------------------------------------------

    private bool ValidateSetup()
    {
        // Guard clauses

        // Validate transmitter reference
        if (transmitter == null)
        {
            Debug.LogError("PropagationGridSimulator: Transmitter is not assigned.");
            return false;
        }

        // Validate reconstructor reference
        if (patternReconstructor == null)
        {
            Debug.LogError("PropagationGridSimulator: PatternGainReconstructor is not assigned.");
            return false;
        }

        // Validate gain matrix availability
        if (!patternReconstructor.IsReady)
        {
            Debug.LogError("PropagationGridSimulator: PatternGainReconstructor is not ready.");
            return false;
        }

        // Validate Python executable
        string pythonPath = GetStreamingAssetsPath(pythonExecutablePath);
        if (!File.Exists(pythonPath))
        {
            Debug.LogError($"PropagationGridSimulator: Python executable not found: {pythonPath}");
            return false;
        }

        // Validate Python bridge
        string bridgePath = GetStreamingAssetsPath(pythonServerScriptPath);
        if (!File.Exists(bridgePath))
        {
            Debug.LogError($"PropagationGridSimulator: Python server script not found: {bridgePath}");
            return false;
        }

        // Validate simulator root
        string simulatorPath = GetStreamingAssetsPath(simulatorRootPath);
        if (!Directory.Exists(simulatorPath))
        {
            Debug.LogError($"PropagationGridSimulator: Simulator not found: {simulatorPath}");
            return false;
        }

        return true;
    }

    private void EnsureParentExists()
    {
        // If parent already assigned, it returns
        if (receiversParent != null)
        {
            return;
        }

        // Creates a default parent object
        GameObject parent = new GameObject("SimulatedReceivers");
        parent.transform.SetParent(transform, false);
        receiversParent = parent.transform;
    }

    // --------------------------------------------------
    // Grid generation
    // --------------------------------------------------

    private RequestPayloadDto BuildGridAndPayload()
    {
        // Initializes debug receivers list
        receivers = new List<VoxelReceiver>();

        // Initializes voxel data list
        voxelsData = new List<VoxelData>(gridSizeMeters.x * gridSizeMeters.y * gridSizeMeters.z);

        // Creates the request object sent to Python
        RequestPayloadDto payload = new RequestPayloadDto();
        payload.scenario = scenario.ToString();
        payload.environmentType = environmentType.ToString();
        payload.lossesModel = lossesModel.ToString();
        payload.frequencyGHz = frequencyGHz;
        payload.txPowerDbm = txPowerDbm;
        payload.rxGainDbi = rxGainDbi;
        payload.minimumDistanceMeters = minimumDistanceMeters;
        payload.disableShadowing = disableShadowing;
        payload.transmitterX = transmitter.position.x;
        payload.transmitterY = transmitter.position.y;
        payload.transmitterZ = transmitter.position.z;
        payload.voxels = new List<VoxelRequestDto>(gridSizeMeters.x * gridSizeMeters.y * gridSizeMeters.z);

        // Gets the corner of the grid
        Vector3 gridOrigin = GetGridOrigin();

        int index = 0;

        // Generates all cell centers in the 3D grid
        // Note: (YZX) order to make it by horizontal layers
        for (int y = 0; y < gridSizeMeters.y; y++)
        {
            for (int z = 0; z < gridSizeMeters.z; z++)
            {
                for (int x = 0; x < gridSizeMeters.x; x++)
                {
                    // Center of the current cubic cell
                    Vector3 center = gridOrigin + new Vector3((x + 0.5f) * cellSizeMeters, (y + 0.5f) * cellSizeMeters, (z + 0.5f) * cellSizeMeters);

                    // Gets TX gain for that direction
                    float txGainDbi = EvaluateTxGainDbi(center);

                    // Counts crossed buildings and computes the extra loss
                    int buildingCollisions = CountBuildingColissions(center);
                    float buildingLossDb = buildingCollisions * lossPerBuildingDb;

                    // Store voxel data
                    VoxelData sample = new VoxelData();
                    sample.index = index;
                    sample.gridX = x;
                    sample.gridY = y;
                    sample.gridZ = z;
                    sample.centerWorldPosition = center;
                    sample.buildingCollisions = buildingCollisions;
                    sample.txPowerDbm = txPowerDbm;
                    sample.txGainDbi = txGainDbi;
                    sample.rxGainDbi = rxGainDbi;

                    // Adds the voxeldata to the list
                    voxelsData.Add(sample);

                    // Creates debug object if a prefab is assigned
                    if (receiverDebugPrefab != null)
                    {
                        GameObject receiverObject = CreateReceiverObject(x, y, z, center);

                        VoxelReceiver receiver = receiverObject.AddComponent<VoxelReceiver>();
                        receiver.data = sample;

                        receivers.Add(receiver);
                    }

                    // Stores voxel request data for Python
                    VoxelRequestDto voxelRequest = new VoxelRequestDto();
                    voxelRequest.index = index;
                    voxelRequest.x = center.x;
                    voxelRequest.y = center.y;
                    voxelRequest.z = center.z;
                    voxelRequest.txGainDbi = txGainDbi;
                    voxelRequest.buildingCollisions = buildingCollisions;
                    voxelRequest.buildingLossDb = buildingLossDb;

                    payload.voxels.Add(voxelRequest);
                    index++;
                }
            }
        }

        return payload;
    }

    private Vector3 GetGridOrigin()
    {
        // Center the grid on the transmitter position
        Vector3 gridCenter = transmitter.position;

        // Computes the total grid size in meters
        Vector3 gridWorldSize = new Vector3(gridSizeMeters.x * cellSizeMeters, gridSizeMeters.y * cellSizeMeters, gridSizeMeters.z * cellSizeMeters);

        // Returns the minimum corner of the grid
        return gridCenter - (gridWorldSize * 0.5f);
    }

    private GameObject CreateReceiverObject(int x, int y, int z, Vector3 center)
    {
        // Instantiates the debug prefab if available
        if (receiverDebugPrefab != null)
        {
            GameObject receiverObject = Instantiate(receiverDebugPrefab, center, Quaternion.identity, receiversParent);
            receiverObject.name = $"Rx_{x}_{y}_{z}";
            return receiverObject;
        }

        // Otherwise create an empty object
        GameObject emptyReceiver = new GameObject($"Rx_{x}_{y}_{z}");
        emptyReceiver.transform.SetParent(receiversParent, false);
        emptyReceiver.transform.position = center;
        return emptyReceiver;
    }

    private float EvaluateTxGainDbi(Vector3 rxWorldPosition)
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
        return patternReconstructor.GetGainDbi(theta, phi);
    }

    private int CountBuildingColissions(Vector3 rxWorldPosition)
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

    // --------------------------------------------------
    // Python bridge
    // --------------------------------------------------

    void StartPythonServer(int port)
    {
        // Resolves paths
        string pythonPath = GetStreamingAssetsPath(pythonExecutablePath);
        string bridgePath = GetStreamingAssetsPath(pythonServerScriptPath);
        string simulatorPath = GetStreamingAssetsPath(simulatorRootPath);

        // Configure the child Python process
        pythonProcess = new Process();
        /*  
            Arguments:
                -u: unbuffered, cleans python standard output so we can read logs in real time
                --port: TCP port for the local server
                --sim-root: path to the SIMULATOR folder

            WorkingDirectory: Set to the Python runtime folder so the portable interpreter starts from its own directory
            UseShellExecute: Not to use the OS shell, required to redirect output
            RedirectStandardOutput: Captures python logs
            RedirectStandardError: Captures python errors
            CreateNoWindow: Avoids showing a console to the user
        */
        pythonProcess.StartInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"-u \"{bridgePath}\" --port {port} --sim-root \"{simulatorPath}\"",
            WorkingDirectory = Path.GetDirectoryName(pythonPath),
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        // Redirects Python logs into Unity
        // When python process writes a line or error, it calls OnPythonOutput or OnPythonError
        pythonProcess.OutputDataReceived += OnPythonOutput;
        pythonProcess.ErrorDataReceived += OnPythonError;

        // Starts the Python process
        pythonProcess.Start();
        pythonProcess.BeginOutputReadLine();
        pythonProcess.BeginErrorReadLine();
    }

    void OnPythonOutput(object sender, DataReceivedEventArgs e)
    {
        // Prints normal Python output in Unity
        if (!string.IsNullOrWhiteSpace(e.Data))
        {
            Debug.Log("[Python] " + e.Data);
        }
    }

    void OnPythonError(object sender, DataReceivedEventArgs e)
    {
        // Prints Python errors in Unity
        if (!string.IsNullOrWhiteSpace(e.Data))
        {
            Debug.LogError("[Python] " + e.Data);
        }
    }

    ResponsePayloadDto SendRequest(int port, RequestPayloadDto payload)
    {
        // Serialize the request object into JSON
        string requestJson = JsonUtility.ToJson(payload);

        // Open the TCP client and dispose it automatically when the block ends
        using (TcpClient client = new TcpClient())
        {
            // Connect to the local Python server
            // NoDelay disables Nagle's algorithm, reducing latency
            client.NoDelay = true;
            client.Connect(IPAddress.Loopback, port);

            // Using to open the network stream and text readers/writers, then dispose them automatically

            // Binary stream of the connection
            using (NetworkStream stream = client.GetStream())
            // Ables to write text in the stream
            using (StreamWriter writer = new StreamWriter(stream, new UTF8Encoding(false), 1024, true))
            // Ables to read text from the stream
            using (StreamReader reader = new StreamReader(stream, Encoding.UTF8, false, 1024, true))
            {
                // Use one JSON message per line
                writer.NewLine = "\n";
                writer.WriteLine(requestJson);
                // Forces the writer to send the data immediately
                writer.Flush();

                // Read the JSON response line
                string responseJson = reader.ReadLine();

                if (string.IsNullOrWhiteSpace(responseJson))
                {
                    throw new IOException("Python returned an empty response.");
                }

                // Deserialize the JSON response
                ResponsePayloadDto response = JsonUtility.FromJson<ResponsePayloadDto>(responseJson);

                if (response == null)
                {
                    throw new IOException("Could not deserialize the Python response.");
                }

                return response;
            }
        }
    }

    void ApplyResponse(ResponsePayloadDto response)
    {
        // Validate response list
        if (response.results == null)
        {
            Debug.LogError("PropagationGridSimulator: Response has no results array.");
            return;
        }

        // Copy each result into the matching voxel data
        for (int i = 0; i < response.results.Count; i++)
        {
            VoxelResultDto result = response.results[i];

            if (result.index < 0 || result.index >= voxelsData.Count)
            {
                Debug.LogWarning($"PropagationGridSimulator: Invalid voxel index in response: {result.index}");
                continue;
            }

            // Copy Python results into voxel data
            VoxelData sample = voxelsData[result.index];
            sample.distanceMeters = result.distanceMeters;
            sample.pathLossDb = result.pathLossDb;
            sample.prxDbm = result.prxDbm;
        }
    }

    // --------------------------------------------------
    // Helpers
    // --------------------------------------------------

    int GetFreePort()
    {
        // Ask the OS for a free local port
        TcpListener listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();

        int port = ((IPEndPoint)listener.LocalEndpoint).Port;

        listener.Stop();
        return port;
    }

    string GetStreamingAssetsPath(string relativePath)
    {
        // Resolve a path relative to StreamingAssets
        return Path.GetFullPath(Path.Combine(Application.streamingAssetsPath, relativePath));
    }

    void ShutdownPython()
    {
        // Nothing to do if the process was never created
        if (pythonProcess == null)
        {
            return;
        }

        try
        {
            // Kill Python if it is still alive
            if (!pythonProcess.HasExited)
            {
                pythonProcess.Kill();
                pythonProcess.WaitForExit(2000); // Wait up to 2 seconds for Python to exit
            }
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"PropagationGridSimulator: Could not stop Python. {ex.Message}");
        }
        finally
        {
            pythonProcess.Dispose(); // Free resources
            pythonProcess = null;
        }
    }

    // --------------------------------------------------
    // DTOs
    // --------------------------------------------------

    [Serializable]
    class RequestPayloadDto
    {
        public string scenario;                  // Channel scenario
        public string environmentType;           // LOS or NLOS
        public string lossesModel;               // ABG or FSPL
        public float frequencyGHz;               // Carrier frequency
        public float txPowerDbm;                 // TX power from Unity
        public float rxGainDbi;                  // RX gain from Unity
        public float minimumDistanceMeters;      // Minimum safe distance
        public bool disableShadowing;            // Disable random shadowing
        public float transmitterX;               // TX world X
        public float transmitterY;               // TX world Y
        public float transmitterZ;               // TX world Z
        public List<VoxelRequestDto> voxels;     // All voxel centers
    }

    [Serializable]
    class VoxelRequestDto
    {
        public int index;                        // Receiver index
        public float x;                          // Receiver world X
        public float y;                          // Receiver world Y
        public float z;                          // Receiver world Z
        public float txGainDbi;                  // TX gain for that direction
        public int buildingCollisions;           // Number of buildings collisions
        public float buildingLossDb;             // Total building loss in dB
    }

    [Serializable]
    class ResponsePayloadDto
    {
        public string error;                     // Error message if something failed
        public List<VoxelResultDto> results;    // Returned simulation values
    }

    [Serializable]
    class VoxelResultDto
    {
        public int index;                        // Receiver index
        public int buildingCollisions;           // Number of buildings collisions
        public float buildingLossDb;             // Total building loss in dB
        public float distanceMeters;             // 3D TX-RX distance
        public float pathLossDb;                 // Propagation losses
        public float prxDbm;                     // Received power
    }
}
