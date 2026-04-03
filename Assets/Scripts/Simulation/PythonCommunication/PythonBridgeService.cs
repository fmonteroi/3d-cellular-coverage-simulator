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

    public bool ValidateSetup()
    {
        string pythonPath = GetStreamingAssetsPath(pythonExecutablePath);
        string bridgePath = GetStreamingAssetsPath(pythonServerScriptPath);
        string simulatorPath = GetStreamingAssetsPath(simulatorRootPath);

        // Validate python executable
        if (!File.Exists(pythonPath))
        {
            Debug.LogError($"PythonBridgeService: Python executable not found: {pythonPath}");
            return false;
        }

        // Validate bridge script
        if (!File.Exists(bridgePath))
        {
            Debug.LogError($"PythonBridgeService: Python bridge script not found: {bridgePath}");
            return false;
        }

        // Validate simulator root
        if (!Directory.Exists(simulatorPath))
        {
            Debug.LogError($"PythonBridgeService: Simulator root not found: {simulatorPath}");
            return false;
        }

        return true;
    }

    public void EnsureStarted()
    {
        // Reuse the running process if possible
        if (isStarted && pythonProcess != null && !pythonProcess.HasExited)
        {
            return;
        }

        if (!ValidateSetup())
        {
            throw new InvalidOperationException("Python bridge setup is invalid.");
        }

        // Reserve one free local port
        port = GetFreePort();

        // Start the Python bridge
        StartPythonServer(port);

        // Give Python time to start listening
        Thread.Sleep(pythonStartupDelayMs);

        isStarted = true;
    }

    public BridgeResponseDto SendRequest(BridgeRequestDto request)
    {
        // Avoid overlapping requests on the same bridge
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
                    // Send one JSON line
                    writer.NewLine = "\n";
                    writer.WriteLine(requestJson);
                    writer.Flush();

                    // Read one JSON response line
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

    public void StopBridge()
    {
        // Nothing to stop if no process exists
        if (pythonProcess == null)
        {
            return;
        }

        try
        {
            try
            {
                // Ask Python to stop gracefully
                BridgeRequestDto shutdownRequest = new BridgeRequestDto();
                shutdownRequest.requestType = "shutdown";
                SendRequest(shutdownRequest);
            }
            catch
            {
                // Fall back to force kill if graceful stop fails
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

    void OnDestroy()
    {
        // Stop the bridge when this object is destroyed
        StopBridge();
    }

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

        // Redirect Python stdout to Unity logs
        pythonProcess.OutputDataReceived += OnPythonOutput;

        // Redirect Python stderr to Unity logs
        pythonProcess.ErrorDataReceived += OnPythonError;

        pythonProcess.Start();
        pythonProcess.BeginOutputReadLine();
        pythonProcess.BeginErrorReadLine();
    }

    private void OnPythonOutput(object sender, DataReceivedEventArgs e)
    {
        // Print normal Python logs
        if (!string.IsNullOrWhiteSpace(e.Data))
        {
            Debug.Log("[Python] " + e.Data);
        }
    }

    private void OnPythonError(object sender, DataReceivedEventArgs e)
    {
        // Print Python errors
        if (!string.IsNullOrWhiteSpace(e.Data))
        {
            Debug.LogError("[Python] " + e.Data);
        }
    }

    private int GetFreePort()
    {
        TcpListener listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();

        int freePort = ((IPEndPoint)listener.LocalEndpoint).Port;

        listener.Stop();
        return freePort;
    }

    private string GetStreamingAssetsPath(string relativePath)
    {
        // Resolve a path relative to StreamingAssets
        return Path.GetFullPath(Path.Combine(Application.streamingAssetsPath, relativePath));
    }
}
