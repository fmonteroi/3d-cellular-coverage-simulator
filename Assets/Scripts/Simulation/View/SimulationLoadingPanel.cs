using TMPro;
using UnityEngine;

public class SimulationLoadingPanel : MonoBehaviour
{
    public GameObject panel;
    public TMP_Text loadingText;

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

    public void Hide()
    {
        if (panel != null)
        {
            panel.SetActive(false);
        }
    }
}