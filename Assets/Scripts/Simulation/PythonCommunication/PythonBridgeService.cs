using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using Debug = UnityEngine.Debug;

/// <summary>
/// Keeps one Python bridge process alive and sends JSON requests to it.
/// </summary>
public class PythonBridgeService : MonoBehaviour
{
    [Header("Python")]
    public string pythonExecutablePath = @"PythonRuntime/python.exe";
    public string pythonServerScriptPath = @"SimulatorBridge/unity_bridge_server.py";
    public string simulatorRootPath = @"SIMULATOR";
    [Min(100)] public int pythonStartupDelayMs = 1000;

    Process pythonProcess;
    int port = -1;
    bool isStarted = false;
    readonly object requestLock = new object();

    /// <summary>
    /// Checks that the Python runtime, bridge script and simulator folder exist.
    /// </summary>
    public bool ValidateSetup()
    {
        string pythonPath = GetStreamingAssetsPath(pythonExecutablePath);
        string bridgePath = GetStreamingAssetsPath(pythonServerScriptPath);
        string simulatorPath = GetStreamingAssetsPath(simulatorRootPath);

        // Validates python executable
        if (!File.Exists(pythonPath))
        {
            Debug.LogError($"PythonBridgeService: Python executable not found: {pythonPath}");
            return false;
        }

        // Validates bridge script
        if (!File.Exists(bridgePath))
        {
            Debug.LogError($"PythonBridgeService: Python bridge script not found: {bridgePath}");
            return false;
        }

        // Validates simulator root
        if (!Directory.Exists(simulatorPath))
        {
            Debug.LogError($"PythonBridgeService: Simulator root not found: {simulatorPath}");
            return false;
        }

        return true;
    }

    /// <summary>
    /// Starts the Python bridge if it is not already running.
    /// </summary>
    public void EnsureStarted()
    {
        // Reuses the running process if possible
        if (isStarted && pythonProcess != null && !pythonProcess.HasExited)
        {
            return;
        }

        if (!ValidateSetup())
        {
            throw new InvalidOperationException("Python bridge setup is invalid.");
        }

        // Reserves one free local port
        port = GetFreePort();

        // Starts the Python bridge
        StartPythonServer(port);

        // Gives Python time to start listening
        Thread.Sleep(pythonStartupDelayMs);

        isStarted = true;
    }

    /// <summary>
    /// Sends one request to Python and waits for one JSON response line.
    /// </summary>
    public BridgeResponseDto SendRequest(BridgeRequestDto request)
    {
        // Avoids overlapping requests on the same bridge
        lock (requestLock)
        {
            EnsureStarted();

            string requestJson = JsonUtility.ToJson(request);

            using (TcpClient client = new TcpClient())
            {
                client.NoDelay = true;
                client.Connect(IPAddress.Loopback, port);

                using (NetworkStream stream = client.GetStream())
                using (StreamWriter writer = new StreamWriter(stream, new UTF8Encoding(false), 1024, true))
                using (StreamReader reader = new StreamReader(stream, Encoding.UTF8, false, 1024, true))
                {
                    // Sends one JSON line
                    writer.NewLine = "\n";
                    writer.WriteLine(requestJson);
                    writer.Flush();

                    // Reads one JSON response line
                    string responseJson = reader.ReadLine();

                    if (string.IsNullOrWhiteSpace(responseJson))
                    {
                        throw new IOException("Python returned an empty response.");
                    }

                    BridgeResponseDto response = JsonUtility.FromJson<BridgeResponseDto>(responseJson);

                    if (response == null)
                    {
                        throw new IOException("Could not deserialize the Python response.");
                    }

                    return response;
                }
            }
        }
    }

    /// <summary>
    /// Stops the Python bridge process.
    /// </summary>
    public void StopBridge()
    {
        // Nothing stops when no process exists
        if (pythonProcess == null)
        {
            return;
        }

        try
        {
            try
            {
                // Asks Python to stop gracefully
                BridgeRequestDto shutdownRequest = new BridgeRequestDto();
                shutdownRequest.requestType = "shutdown";
                SendRequest(shutdownRequest);
            }
            catch
            {
                // Falls back to force kill if graceful stop fails
            }

            if (!pythonProcess.HasExited)
            {
                pythonProcess.Kill();
                pythonProcess.WaitForExit(2000);
            }
        }
        finally
        {
            pythonProcess.Dispose();
            pythonProcess = null;
            isStarted = false;
            port = -1;
        }
    }

    /// <summary>
    /// Stops the bridge when the Unity object is destroyed.
    /// </summary>
    void OnDestroy()
    {
        // Stops the bridge when this object is destroyed
        StopBridge();
    }

    /// <summary>
    /// Starts the Python TCP server process on the selected port.
    /// </summary>
    private void StartPythonServer(int selectedPort)
    {
        string pythonPath = GetStreamingAssetsPath(pythonExecutablePath);
        string bridgePath = GetStreamingAssetsPath(pythonServerScriptPath);
        string simulatorPath = GetStreamingAssetsPath(simulatorRootPath);

        pythonProcess = new Process();
        pythonProcess.StartInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"-u \"{bridgePath}\" --port {selectedPort} --sim-root \"{simulatorPath}\"",
            WorkingDirectory = Path.GetDirectoryName(pythonPath),
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        // Redirects Python stdout to Unity logs
        pythonProcess.OutputDataReceived += OnPythonOutput;

        // Redirects Python stderr to Unity logs
        pythonProcess.ErrorDataReceived += OnPythonError;

        pythonProcess.Start();
        pythonProcess.BeginOutputReadLine();
        pythonProcess.BeginErrorReadLine();
    }

    /// <summary>
    /// Sends normal Python output to the Unity console.
    /// </summary>
    private void OnPythonOutput(object sender, DataReceivedEventArgs e)
    {
        // Prints normal Python logs
        if (!string.IsNullOrWhiteSpace(e.Data))
        {
            Debug.Log("[Python] " + e.Data);
        }
    }

    /// <summary>
    /// Sends Python error output to the Unity console.
    /// </summary>
    private void OnPythonError(object sender, DataReceivedEventArgs e)
    {
        // Prints Python errors
        if (!string.IsNullOrWhiteSpace(e.Data))
        {
            Debug.LogError("[Python] " + e.Data);
        }
    }

    /// <summary>
    /// Reserves and returns one free local TCP port.
    /// </summary>
    private int GetFreePort()
    {
        TcpListener listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();

        int freePort = ((IPEndPoint)listener.LocalEndpoint).Port;

        listener.Stop();
        return freePort;
    }

    /// <summary>
    /// Resolves a path relative to StreamingAssets.
    /// </summary>
    private string GetStreamingAssetsPath(string relativePath)
    {
        // Resolves a path relative to StreamingAssets
        return Path.GetFullPath(Path.Combine(Application.streamingAssetsPath, relativePath));
    }
}
