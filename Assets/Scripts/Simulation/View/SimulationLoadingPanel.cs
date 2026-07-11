using TMPro;
using UnityEngine;

/// <summary>
/// Shows and hides the loading panel used during simulation startup.
/// </summary>
public class SimulationLoadingPanel : MonoBehaviour
{
    public GameObject panel;
    public TMP_Text loadingText;

    /// <summary>
    /// Shows the loading panel with the selected message.
    /// </summary>
    public void Show(string message)
    {
        if (loadingText != null)
        {
            loadingText.text = message;
        }

        if (panel != null)
        {
            panel.SetActive(true);
        }
    }

    /// <summary>
    /// Hides the loading panel.
    /// </summary>
    public void Hide()
    {
        if (panel != null)
        {
            panel.SetActive(false);
        }
    }
}
