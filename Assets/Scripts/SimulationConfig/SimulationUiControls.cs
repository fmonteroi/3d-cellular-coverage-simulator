using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

/// <summary>
/// Handles common simulation UI actions such as pause and return to menu.
/// </summary>
public class SimulationUiControls : MonoBehaviour
{
    [Header("References")]
    public ReceiverResultsManager resultsManager;

    [Header("Scenes")]
    public string mainMenuSceneName = "MainMenu";

    [Header("Pause icon")]
    public Image pauseButtonIcon;
    public Sprite pauseSprite;
    public Sprite playSprite;

    private bool isPaused = false;

    /// <summary>
    /// Exports pending results and loads the main menu scene.
    /// </summary>
    public void BackToMainMenu()
    {
        // Saves partial receiver results before leaving the simulation
        if (resultsManager != null)
        {
            resultsManager.ExportPending();
        }

        // Restores normal time before changing scene
        Time.timeScale = 1f;
        SceneManager.LoadScene(mainMenuSceneName);
    }

    /// <summary>
    /// Toggles the simulation pause state and updates the pause button icon.
    /// </summary>
    public void TogglePause()
    {
        isPaused = !isPaused;

        if (isPaused)
        {
            Time.timeScale = 0f;
        }
        else
        {
            Time.timeScale = 1f;
        }

        if (pauseButtonIcon != null)
        {
            if (isPaused)
            {
                pauseButtonIcon.sprite = playSprite;
            }
            else
            {
                pauseButtonIcon.sprite = pauseSprite;
            }
        }
    }
}
