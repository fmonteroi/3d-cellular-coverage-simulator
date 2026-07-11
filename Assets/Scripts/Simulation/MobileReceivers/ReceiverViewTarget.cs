using UnityEngine;

/// <summary>
/// Defines how the camera should follow one receiver.
/// </summary>
public class ReceiverViewTarget : MonoBehaviour
{
    public Vector3 cameraOffset = new Vector3(0f, 6f, -8f);
    public Vector3 lookOffset = new Vector3(0f, 1.5f, 0f);

    /// <summary>
    /// Gets the desired camera position for this receiver view.
    /// </summary>
    public Vector3 GetCameraPosition()
    {
        return transform.position + cameraOffset;
    }

    /// <summary>
    /// Gets the point the camera should look at for this receiver view.
    /// </summary>
    public Vector3 GetLookPosition()
    {
        return transform.position + lookOffset;
    }
}
