using TMPro;
using UnityEngine;
using UnityEngine.UI;
using System.Collections;

/// <summary>
/// Displays a 2D heatmap slice of the 3D propagation grid over a zenithal campus map.
/// </summary>
public class Heatmap2DPanel : MonoBehaviour
{
    // --------------------------------------------------
    // Inspector references
    // --------------------------------------------------

    [Header("Source")]
    public PropagationGridSimulator simulator;

    [Header("UI")]
    public RawImage mapImage;
    public RawImage heatmapImage;
    public RectTransform antennaMapMarker;
    public Slider heightSlider;
    public TMP_Text heightText;

    [Header("Expanded view")]
    public GameObject expandedPanel;
    public RawImage expandedMapImage;
    public RawImage expandedHeatmapImage;
    public RectTransform expandedAntennaMapMarker;
    public Slider expandedHeightSlider;
    public TMP_Text expandedHeightText;
    public TMP_Text maxPrxText;
    public TMP_Text minPrxText;
    public Image antennaHeightMarkerImage;

    [Header("Zenithal camera")]
    public Camera zenithalCamera;
    public RenderTexture zenithalRenderTexture;
    public float cameraHeightOffset = 100f;

    [Header("Campus map bounds")]
    public Transform mapMinPoint;
    public Transform mapMaxPoint;

    [Header("Heatmap style")]
    public int heatmapResolution = 512;
    [Range(0f, 1f)] public float heatmapAlpha = 0.8f;

    [Header("Objects hidden in expanded view")]
    public GameObject[] objectsHiddenInExpandedView;

    public bool IsExpandedViewOpen { get; private set; }
    private Texture2D heatmapTexture;
    private float minPrx;
    private float maxPrx;
    private float visibleWidthMeters;
    private float visibleDepthMeters;
    private int currentHeightLayer;


    /// <summary>
    /// Finds the simulator and initializes the 2D heatmap when voxel data is available.
    /// </summary>
    private IEnumerator Start()
    {
        // Stop if no simulator was assigned
        if (simulator == null)
        {
            yield break;
        }

        // Wait until the grid simulation has finished
        while (!simulator.ResultsReady)
        {
            yield return null;
        }

        // Stop if the simulator finished but has no voxel data
        if (simulator.voxelsData == null || simulator.voxelsData.Count == 0)
        {
            yield break;
        }

        // Build the initial heatmap
        InitializeHeatmap();
    }

    // --------------------------------------------------
    // Initialization
    // --------------------------------------------------

    /// <summary>
    /// Prepares the minimap camera, heatmap texture, slider range, and first visible layer.
    /// </summary>
    private void InitializeHeatmap()
    {
        // Compute the global Prx range used for color normalization
        FindPrxRange();

        // Updates the min and max Prx labels in the expanded view
        if (maxPrxText != null)
        {
            maxPrxText.text = $"{maxPrx:F2} dBm";
        }

        if (minPrxText != null)
        {
            minPrxText.text = $"{minPrx:F2} dBm";
        }

        // Get the real voxel count, not only the grid size in meters
        Vector3Int voxelCount = simulator.VoxelCount;

        // Configure the zenithal camera to match the campus map bounds
        ConfigureZenithalCamera();

        // Compute the real-world area visible in the minimap
        CalculateVisibleMapSize();

        // Create a fixed-resolution texture for the full minimap
        heatmapTexture = new Texture2D(heatmapResolution, heatmapResolution, TextureFormat.RGBA32, false);
        heatmapTexture.filterMode = FilterMode.Bilinear;
        heatmapTexture.wrapMode = TextureWrapMode.Clamp;

        // Assign the generated texture to the UI image
        if (heatmapImage != null)
        {
            heatmapImage.texture = heatmapTexture;
        }

        // Configure the height slider to select voxel layers
        if (heightSlider != null)
        {
            heightSlider.minValue = 0;
            heightSlider.maxValue = voxelCount.y - 1;
            heightSlider.wholeNumbers = true;
            heightSlider.onValueChanged.AddListener(OnHeightChanged);
        }

        // Configure the expanded view UI elements
        if (expandedHeightSlider != null)
        {
            expandedHeightSlider.minValue = 0;
            expandedHeightSlider.maxValue = voxelCount.y - 1;
            expandedHeightSlider.wholeNumbers = true;
            expandedHeightSlider.onValueChanged.AddListener(OnHeightChanged);
        }

        // Start at the middle height layer
        int initialLayer = voxelCount.y / 2;
        currentHeightLayer = initialLayer;

        if (heightSlider != null)
        {
            heightSlider.SetValueWithoutNotify(initialLayer);
        }

        if (expandedHeightSlider != null)
        {
            expandedHeightSlider.SetValueWithoutNotify(initialLayer);
        }

        Draw2DHeatmap(initialLayer);
        UpdateAntennaMapMarkers();
    }

    /// <summary>
    /// Finds the minimum and maximum Prx values across the full voxel grid.
    /// </summary>
    private void FindPrxRange()
    {
        minPrx = float.PositiveInfinity;
        maxPrx = float.NegativeInfinity;

        // Search the minimum and maximum Prx values across all voxels
        for (int i = 0; i < simulator.voxelsData.Count; i++)
        {
            float value = simulator.voxelsData[i].prxDbm;

            if (value < minPrx)
            {
                minPrx = value;
            }

            if (value > maxPrx)
            {
                maxPrx = value;
            }
        }
    }

    // --------------------------------------------------
    // Slider handling
    // --------------------------------------------------

    /// <summary>
    /// Redraws the heatmap when the selected height layer changes.
    /// </summary>
    private void OnHeightChanged(float value)
    {
        int layer = Mathf.RoundToInt(value);
        currentHeightLayer = layer;

        if (heightSlider != null && Mathf.RoundToInt(heightSlider.value) != layer)
        {
            // SetValueWithoutNotify is used to avoid triggering another OnHeightChanged event
            heightSlider.SetValueWithoutNotify(layer);
        }

        if (expandedHeightSlider != null && Mathf.RoundToInt(expandedHeightSlider.value) != layer)
        {
            // SetValueWithoutNotify is used to avoid triggering another OnHeightChanged event
            expandedHeightSlider.SetValueWithoutNotify(layer);
        }

        // Redraw the heatmap when the selected height layer changes
        Draw2DHeatmap(layer);
    }

    // --------------------------------------------------
    // Heatmap drawing
    // --------------------------------------------------

    /// <summary>
    /// Draws one horizontal voxel layer into the 2D heatmap texture.
    /// </summary>
    private void Draw2DHeatmap(int gridY)
    {
        if (heatmapTexture == null)
        {
            return;
        }

        // Clear previous pixels before drawing the new layer
        Color clearColor = new Color(0f, 0f, 0f, 0f);

        for (int z = 0; z < heatmapTexture.height; z++)
        {
            for (int x = 0; x < heatmapTexture.width; x++)
            {
                heatmapTexture.SetPixel(x, z, clearColor);
            }
        }

        // Draw only voxels that belong to the selected height layer
        for (int i = 0; i < simulator.voxelsData.Count; i++)
        {
            VoxelData voxel = simulator.voxelsData[i];

            if (voxel.gridY != gridY)
            {
                continue;
            }

            float normalizedPrx = Normalize(voxel.prxDbm, minPrx, maxPrx);
            Color color = EvaluateHeatColor(normalizedPrx);

            // Paint the voxel using its rotated footprint on the 2D map.
            PaintRotatedVoxel(voxel.centerWorldPosition, color);
        }

        // Upload pixel changes to the GPU
        heatmapTexture.Apply();

        // Update the height label
        if (heightText != null)
        {
            heightText.text = $"Height layer: {gridY + 1}";
        }

        if (expandedHeightText != null)
        {
            float relativeHeight = GetLayerHeightRelativeToAntenna(gridY);

            expandedHeightText.text = $"Height layer: {gridY + 1}\n{relativeHeight:F2} m";
        }
    }

    /// <summary>
    /// Paints one voxel on the heatmap using the real grid rotation.
    /// The voxel is converted into four rotated corners, then the smallest pixel area
    /// that covers those corners is filled. This avoids empty pixels when the grid is rotated.
    /// </summary>
    private void PaintRotatedVoxel(Vector3 centerWorldPosition, Color color)
    {
        // Half of the voxel size is used to build the four local floor corners.
        float half = simulator.voxelSizeMeters * 0.5f;

        // The grid uses the same rotation as the transmitter.
        Quaternion rotation = simulator.settings.transmitter.rotation;

        // Convert the four rotated voxel corners from world space to heatmap pixels.
        Vector2[] corners = new Vector2[]
        {
        WorldToHeatmapPixelFloat(centerWorldPosition + rotation * new Vector3(-half, 0f, -half)),
        WorldToHeatmapPixelFloat(centerWorldPosition + rotation * new Vector3( half, 0f, -half)),
        WorldToHeatmapPixelFloat(centerWorldPosition + rotation * new Vector3( half, 0f,  half)),
        WorldToHeatmapPixelFloat(centerWorldPosition + rotation * new Vector3(-half, 0f,  half)),
        };

        // Find the pixel rectangle that contains the rotated voxel footprint.
        float minXf = Mathf.Min(corners[0].x, corners[1].x, corners[2].x, corners[3].x);
        float maxXf = Mathf.Max(corners[0].x, corners[1].x, corners[2].x, corners[3].x);
        float minYf = Mathf.Min(corners[0].y, corners[1].y, corners[2].y, corners[3].y);
        float maxYf = Mathf.Max(corners[0].y, corners[1].y, corners[2].y, corners[3].y);

        // Floor and Ceil include border pixels so small rounding errors do not create gaps.
        int minX = Mathf.Clamp(Mathf.FloorToInt(minXf), 0, heatmapTexture.width - 1);
        int maxX = Mathf.Clamp(Mathf.CeilToInt(maxXf), 0, heatmapTexture.width - 1);
        int minY = Mathf.Clamp(Mathf.FloorToInt(minYf), 0, heatmapTexture.height - 1);
        int maxY = Mathf.Clamp(Mathf.CeilToInt(maxYf), 0, heatmapTexture.height - 1);

        // Fill the selected pixel area with the voxel color.
        for (int y = minY; y <= maxY; y++)
        {
            for (int x = minX; x <= maxX; x++)
            {
                heatmapTexture.SetPixel(x, y, color);
            }
        }
    }

    /// <summary>
    /// Converts normalized Prx into a semi-transparent yellow-to-red color.
    /// </summary>
    private Color EvaluateHeatColor(float normalizedPrx)
    {
        // Convert normalized power to a yellow-red heat color
        normalizedPrx = Mathf.Clamp01(normalizedPrx);

        Color color = Color.Lerp(Color.yellow, Color.red, normalizedPrx);
        color.a = heatmapAlpha;

        return color;
    }

    /// <summary>
    /// Normalizes a value between a minimum and maximum into the 0..1 range.
    /// </summary>
    private float Normalize(float value, float minValue, float maxValue)
    {
        // Convert value to the 0..1 range
        float range = maxValue - minValue;

        if (range <= 0.001f)
        {
            return 1f;
        }

        return Mathf.Clamp01((value - minValue) / range);
    }

    // --------------------------------------------------
    // Conversions
    // --------------------------------------------------

    /// <summary>
    /// Calculates the real-world width and depth covered by the minimap camera.
    /// </summary>
    private void CalculateVisibleMapSize()
    {
        if (mapMinPoint == null || mapMaxPoint == null)
        {
            return;
        }

        Vector3 min = mapMinPoint.position;
        Vector3 max = mapMaxPoint.position;

        // Get the requested campus bounds in world meters
        float mapWidth = Mathf.Abs(max.x - min.x);
        float mapDepth = Mathf.Abs(max.z - min.z);

        float textureAspect = 1f;

        if (zenithalRenderTexture != null)
        {
            textureAspect = zenithalRenderTexture.width / (float)zenithalRenderTexture.height;
        }

        float mapAspect = mapWidth / mapDepth;

        // Match the real visible area used by the orthographic camera
        if (mapAspect > textureAspect)
        {
            visibleWidthMeters = mapWidth;
            visibleDepthMeters = mapWidth / textureAspect;
        }
        else
        {
            visibleDepthMeters = mapDepth;
            visibleWidthMeters = mapDepth * textureAspect;
        }
    }

    /// <summary>
    /// Converts a world position into a heatmap pixel position with decimals.
    /// </summary>
    private Vector2 WorldToHeatmapPixelFloat(Vector3 worldPosition)
    {
        // The map bounds define the world area represented by the 2D heatmap.
        Vector3 min = mapMinPoint.position;
        Vector3 max = mapMaxPoint.position;

        // The minimap is centered between both bounds.
        Vector3 center = (min + max) * 0.5f;

        // Use the real visible area calculated from the camera/render texture aspect ratio.
        float minVisibleX = center.x - visibleWidthMeters * 0.5f;
        float maxVisibleX = center.x + visibleWidthMeters * 0.5f;

        float minVisibleZ = center.z - visibleDepthMeters * 0.5f;
        float maxVisibleZ = center.z + visibleDepthMeters * 0.5f;

        // Convert world X/Z coordinates into normalized 0..1 map coordinates.
        float normalizedX = Mathf.InverseLerp(minVisibleX, maxVisibleX, worldPosition.x);
        float normalizedZ = Mathf.InverseLerp(minVisibleZ, maxVisibleZ, worldPosition.z);

        // Convert normalized map coordinates into texture pixel coordinates.
        float pixelX = normalizedX * (heatmapTexture.width - 1);
        float pixelY = normalizedZ * (heatmapTexture.height - 1);

        return new Vector2(pixelX, pixelY);
    }

    // --------------------------------------------------
    // Zenithal camera
    // --------------------------------------------------

    /// <summary>
    /// Positions and scales the zenithal camera so it renders the selected campus bounds.
    /// </summary>
    private void ConfigureZenithalCamera()
    {
        if (zenithalCamera == null || zenithalRenderTexture == null || mapMinPoint == null || mapMaxPoint == null)
        {
            return;
        }

        Vector3 min = mapMinPoint.position;
        Vector3 max = mapMaxPoint.position;

        // Place the camera above the center of the campus bounds
        Vector3 center = (min + max) * 0.5f;

        zenithalCamera.transform.position = center + Vector3.up * cameraHeightOffset;
        zenithalCamera.transform.LookAt(center);

        zenithalCamera.orthographic = true;
        zenithalCamera.nearClipPlane = 0.3f;
        zenithalCamera.farClipPlane = cameraHeightOffset + 200f;

        float mapWidth = Mathf.Abs(max.x - min.x);
        float mapDepth = Mathf.Abs(max.z - min.z);

        float textureAspect = zenithalRenderTexture.width / (float)zenithalRenderTexture.height;
        float mapAspect = mapWidth / mapDepth;

        // Fit the full campus bounds into the render texture
        if (mapAspect > textureAspect)
        {
            zenithalCamera.orthographicSize = (mapWidth / textureAspect) * 0.5f;
        }
        else
        {
            zenithalCamera.orthographicSize = mapDepth * 0.5f;
        }

        zenithalCamera.targetTexture = zenithalRenderTexture;
    }

    // --------------------------------------------------
    // Expanded view
    // --------------------------------------------------

    /// <summary>
    /// Opens the expanded 2D heatmap view.
    /// </summary>
    public void ShowExpandedHeatmap()
    {
        SetExpandedView(true);
    }

    /// <summary>
    /// Closes the expanded 2D heatmap view.
    /// </summary>
    public void HideExpandedHeatmap()
    {
        SetExpandedView(false);
    }

    /// <summary>
    /// Shows or hides the expanded view and the objects that should not be visible behind it.
    /// </summary>
    private void SetExpandedView(bool expanded)
    {
        IsExpandedViewOpen = expanded;

        if (objectsHiddenInExpandedView == null)
        {
            return;
        }

        if (expandedPanel != null)
        {
            expandedPanel.SetActive(expanded);
        }

        for (int i = 0; i < objectsHiddenInExpandedView.Length; i++)
        {
            if (objectsHiddenInExpandedView[i] != null)
            {
                objectsHiddenInExpandedView[i].SetActive(!expanded);
            }
        }

        if (expanded)
        {
            RefreshExpandedView();
        }
    }

    /// <summary>
    /// Updates expanded view textures, labels, and slider value from the current heatmap state.
    /// </summary>
    private void RefreshExpandedView()
    {
        if (expandedMapImage != null)
        {
            expandedMapImage.texture = zenithalRenderTexture;
        }

        if (expandedHeatmapImage != null)
        {
            expandedHeatmapImage.texture = heatmapTexture;
        }

        if (maxPrxText != null)
        {
            maxPrxText.text = $"{maxPrx:F2} dBm";
        }

        if (minPrxText != null)
        {
            minPrxText.text = $"{minPrx:F2} dBm";
        }

        if (expandedHeightSlider != null)
        {
            // SetValueWithoutNotify is used to avoid triggering another OnHeightChanged event
            expandedHeightSlider.SetValueWithoutNotify(currentHeightLayer);
        }

        if (expandedHeightText != null)
        {
            float relativeHeight = GetLayerHeightRelativeToAntenna(currentHeightLayer);

            expandedHeightText.text = $"Height layer: {currentHeightLayer + 1}\n{relativeHeight:F2} m";
        }
    }

    /// <summary>
    /// Places the antenna marker on both the small heatmap and the expanded heatmap.
    /// The antenna is only a point on the map, so it does not need the voxel rotation logic.
    /// </summary>
    private void UpdateAntennaMapMarkers()
    {
        if (antennaMapMarker == null || heatmapImage == null || simulator == null || simulator.settings == null || simulator.settings.transmitter == null)
        {
            return;
        }

        // Convert the transmitter world position to a heatmap pixel position.
        Vector2 antennaPixel = WorldToHeatmapPixelFloat(simulator.settings.transmitter.position);

        // UI anchors use normalized 0..1 coordinates, not raw pixels.
        float normalizedX = antennaPixel.x / (float)(heatmapTexture.width - 1);

        float normalizedY = antennaPixel.y / (float)(heatmapTexture.height - 1);

        SetMarkerPosition(antennaMapMarker, heatmapImage, normalizedX, normalizedY);
        SetMarkerPosition(expandedAntennaMapMarker, expandedHeatmapImage, normalizedX, normalizedY);
    }

    /// <summary>
    /// Moves a UI marker to a normalized position inside a RawImage.
    /// </summary>
    private void SetMarkerPosition(RectTransform marker, RawImage targetImage, float normalizedX, float normalizedY)
    {
        if (marker == null || targetImage == null)
        {
            return;
        }

        Vector2 normalizedPosition = new Vector2(Mathf.Clamp01(normalizedX), Mathf.Clamp01(normalizedY));

        marker.anchorMin = normalizedPosition;
        marker.anchorMax = normalizedPosition;
        marker.anchoredPosition = Vector2.zero;
    }

    /// <summary>
    /// Converts a grid layer index into a height value relative to the antenna center.
    /// </summary>
    private float GetLayerHeightRelativeToAntenna(int gridY)
    {
        float gridBottom = -simulator.gridSizeMeters.y * 0.5f;
        float voxelCenter = (gridY + 0.5f) * simulator.voxelSizeMeters;

        return gridBottom + voxelCenter;
    }
}
