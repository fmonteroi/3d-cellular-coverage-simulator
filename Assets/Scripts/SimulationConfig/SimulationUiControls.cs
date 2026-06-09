using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class SimulationUiControls : MonoBehaviour
{
    [Header("Scenes")]
    public string mainMenuSceneName = "MainMenu";

    [Header("Pause icon")]
    public Image pauseButtonIcon;
    public Sprite pauseSprite;
    public Sprite playSprite;

    private bool isPaused = false;

    public void BackToMainMenu()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene(mainMenuSceneName);
    }

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