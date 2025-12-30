using System;
using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Linq;

public class BookLoader : MonoBehaviour
{
    [Header("Server")]
    public static string BaseUrl = "http://127.0.0.1:8000";

    [Header("Menu")] 
    [SerializeField] private GameObject menuPanel;
    [SerializeField] private Transform bookListContainer;
    [SerializeField] private GameObject bookPreviewPrefab;
    
    [Header("Reader")]
    [SerializeField] private GameObject readerPanel;
    [SerializeField] private TextMeshProUGUI bookTitle;
    [SerializeField] private TextMeshProUGUI sceneText;

    [SerializeField] private Button prevSceneButton;
    [SerializeField] private Button nextSceneButton;

    [Header("Skybox")] 
    [SerializeField] private Material menuSkyboxMat;
    private Material _skyboxMaterialInstance;
    private Coroutine _skyboxTransitionRoutine;
    private const float _skyboxTransitionDuration = 0.75f;

    [Header("Floor")]
    [SerializeField] private Renderer floorQuadRenderer;
    [SerializeField] private Color floorDefaultColor;
    private string _floorColorProperty = "_BaseColor";
    private Material _floorMaterialInstance;
    
    private Book _currentBook;
    private int _currentSceneIndex = -1;
    
    [Serializable]
    public class BookOverviewList
    {
        public BookOverview[] books;
    }

    [Serializable]
    public class BookOverview
    {
        public string id;
        public string title;
        public string author;
        public int num_scenes;
        public string cover;
    }
    
    [Serializable]
    public class Book
    {
        public string id;
        public string title;
        public object author;
        public DateTime created_at;
        public int num_scenes;
        public List<Scene> scenes;
    }

    [Serializable]
    public class Scene
    {
        public int index;
        public string text;
        public string image_prompt;
        public string image_file;
    }
    
    private void Start()
    {
        // fetch book previews from server
        StartCoroutine(FetchBooks());
        
        // deactivate book reader panel
        readerPanel.SetActive(false);

        // set skybox & floor
        if (menuSkyboxMat != null)
        {
            _skyboxMaterialInstance = new Material(menuSkyboxMat);
            RenderSettings.skybox = _skyboxMaterialInstance;
        }
        if (floorQuadRenderer != null)
        {
            _floorMaterialInstance = floorQuadRenderer.material;
        }
    }
    
    /// <summary>
    /// Fetches book previews from server and creates one tile per book in the main menu
    /// </summary>
    private IEnumerator FetchBooks()
    {
        string url = BaseUrl + "/books";

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Error fetching books: " + request.error);
                yield break;
            }
            
            // parse json response
            string json = request.downloadHandler.text;

            BookOverviewList bookList = JsonUtility.FromJson<BookOverviewList>(json);
            if (bookList == null || bookList.books == null)
            {
                Debug.LogWarning("No books parsed from response.");
                yield break;
            }

            // create clickable tile for each book
            foreach (Transform child in bookListContainer)
            {
                Destroy(child.gameObject);
            }
            foreach (BookOverview book in bookList.books.OrderBy(b => b.id))
            {
                CreateBookTile(book);
            }
        }
    }
    
    /// <summary>
    /// Creates a clickable tile with book preview infos
    /// </summary>
    /// <param name="book">book preview object</param>
    private void CreateBookTile(BookOverview book)
    {
        // instantiate button
        GameObject tile = Instantiate(bookPreviewPrefab, bookListContainer);
        tile.name = "BookButton_" + book.id;

        // fill UI components
        UIComponents comps = tile.GetComponentInChildren<UIComponents>();
        if (comps != null)
        {
            comps.title.text = book.title;
            string author = string.IsNullOrEmpty(book.author) ? "unbekannt" : book.author;
            comps.author.text = $"Autor: {author}";
            comps.numscenes.text = $"{book.num_scenes} Szenen";
            
            if (comps.cover != null && !string.IsNullOrEmpty(book.cover))
            {
                StartCoroutine(LoadCover($"{book.id}/{book.cover}", comps.cover));
            }
        }

        // add listener: get entire Book on click
        Button btn = tile.GetComponent<Button>();
        btn.onClick.AddListener(() =>
        {
            Debug.Log("Clicked book: " + book.id);
            StartCoroutine(FetchBookById(book.id));
        });
    }
    
    /// <summary>
    /// fetches book cover from server and sets it as the book's preview image
    /// </summary>
    /// <param name="imageFile">path of the image file on server</param>
    /// <param name="target">image to replace</param>
    private IEnumerator LoadCover(string imageFile, RawImage target)
    {
        string url = $"{BaseUrl}/static/{imageFile}";

        using (UnityWebRequest req = UnityWebRequestTexture.GetTexture(url))
        {
            yield return req.SendWebRequest();

            if (req.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Cover load failed: {url} ({req.error})");
                yield break;
            }

            if (target == null) yield break;

            Texture2D tex = DownloadHandlerTexture.GetContent(req);
            target.texture = tex;
        }
    }
    
    /// <summary>
    /// Fetches book scenes (text only) from server
    /// </summary>
    /// <param name="bookId">ID of the book to fetch</param>
    private IEnumerator FetchBookById(string bookId)
    {
        string url = BaseUrl + "/books/" + bookId;
        Debug.Log("GET " + url);

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Error fetching book " + bookId + ": " + request.error);
                yield break;
            }

            string json = request.downloadHandler.text;

            // JSON in ein Book-Objekt parsen
            Book book = JsonUtility.FromJson<Book>(json);
            
            menuPanel.SetActive(false);
            DisplayBook(book);
        }
    }

    public void DisplayMenu()
    {
        _currentSceneIndex = -1;
        ResetSkybox();
        menuPanel.SetActive(true);
        readerPanel.SetActive(false);
    }
    
    public void DisplayBook(Book book)
    {
        _currentBook = book;
        readerPanel.SetActive(true);
        bookTitle.text = book.title;

        _currentSceneIndex = -1;
        
        // Show first Scene
        NextScene();
    }

    public void NextScene()
    {
        if (_currentBook == null) return;
        if (_currentSceneIndex >= _currentBook.scenes.Count - 1) return;

        _currentSceneIndex++;

        ShowScene();
    }

    public void PrevScene()
    {
        if (_currentBook == null) return;
        if (_currentSceneIndex <= 0) return;

        _currentSceneIndex--;

        ShowScene();
    }

    /// <summary>
    /// Switches to the scene indicated by the current scene index
    /// </summary>
    private void ShowScene()
    {
        if (_currentBook == null) return;
        if (_currentSceneIndex < 0 || _currentSceneIndex >= _currentBook.scenes.Count) return;
        
        // enable / disable navigation buttons
        prevSceneButton.gameObject.SetActive(_currentSceneIndex > 0);
        nextSceneButton.gameObject.SetActive(_currentSceneIndex < _currentBook.scenes.Count - 1);

        Scene scene = _currentBook.scenes[_currentSceneIndex];

        // Show Scene text
        sceneText.text = scene.text;

        // Show Skybox
        if (!string.IsNullOrEmpty(scene.image_file))
        {
            StartCoroutine(FetchAndUpdateSkybox(scene.image_file));
        }
        else
        {
            ResetSkybox();
        }
    }


    /// <summary>
    /// Fetches 360° panorama image from server and sets it as the skybox
    /// </summary>
    /// <param name="imageFile">path of the image file on server</param>
    /// <returns></returns>
    private IEnumerator FetchAndUpdateSkybox(string imageFile)
    {
        if (_skyboxMaterialInstance == null)
            yield break;
        if (_currentBook == null)
            yield break;

        string url = $"{BaseUrl}/static/{imageFile}";

        using (UnityWebRequest request = UnityWebRequestTexture.GetTexture(url))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Error loading skybox texture: " + request.error);
                yield break;
            }
            
            Texture2D tex = DownloadHandlerTexture.GetContent(request);
            
            SetSkybox(tex);
        }
    }

    private void SetSkybox(Texture2D texture)
    {
        Material mat = new Material(Shader.Find("Skybox/Panoramic"));
        mat.SetTexture("_MainTex", texture);
        mat.SetFloat("_Rotation", 90f);
        
        Color col = CalculateFloorColor(texture);
            
        SetSkybox(mat, col);
    }
    
    private void SetSkybox(Material skybox, Color floorColor)
    {
        if (_skyboxMaterialInstance != null)
        {
            if (_skyboxTransitionRoutine != null)
                StopCoroutine(_skyboxTransitionRoutine);

            _skyboxTransitionRoutine = StartCoroutine(SmoothSkyboxTransition(skybox, floorColor, _skyboxTransitionDuration));
        }
    }

    private void ResetSkybox()
    {
        SetSkybox(menuSkyboxMat, floorDefaultColor);
    }
    
    /// <summary>
    /// Calculates the color of the floor from pixels at the bottom of panorama image
    /// </summary>
    /// <param name="tex"></param>
    /// <returns></returns>
    private Color CalculateFloorColor(Texture2D tex)
    {
        if (_floorMaterialInstance == null || tex == null)
            return floorDefaultColor;

        int width = tex.width;
        int height = tex.height;

        int regionHeight = Mathf.Max(1, height / 12);
        int regionY = 0;

        Color[] pixels = tex.GetPixels(0, regionY, width, regionHeight);
        if (pixels == null || pixels.Length == 0)
            return floorDefaultColor;

        float r = 0f, g = 0f, b = 0f, a = 0f;
        int count = pixels.Length;

        for (int i = 0; i < count; i++)
        {
            Color c = pixels[i];
            r += c.r;
            g += c.g;
            b += c.b;
            a += c.a;
        }

        return new Color(r / count, g / count, b / count, a / count);
    }
    
    private IEnumerator SmoothSkyboxTransition(Material targetSkybox, Color targetFloorColor, float duration)
    {
        if (_skyboxMaterialInstance == null)
            yield break;

        Material currentMat = _skyboxMaterialInstance;
        Color startFloorColor = (_floorMaterialInstance != null)
            ? _floorMaterialInstance.GetColor(_floorColorProperty)
            : floorDefaultColor;

        bool curHasExposure = currentMat.HasProperty("_Exposure");
        float startExposure = curHasExposure ? currentMat.GetFloat("_Exposure") : 1f;

        Material nextMat = new Material(targetSkybox);
        bool nextHasExposure = nextMat.HasProperty("_Exposure");
        float targetExposure = nextHasExposure ? nextMat.GetFloat("_Exposure") : 1f;

        // Fade out current
        float half = Mathf.Max(0.0001f, duration * 0.5f);
        float t = 0f;
        while (t < half)
        {
            float u = t / half;

            if (curHasExposure)
                currentMat.SetFloat("_Exposure", Mathf.Lerp(startExposure, 0f, u));

            if (_floorMaterialInstance != null)
                _floorMaterialInstance.SetColor(_floorColorProperty, Color.Lerp(startFloorColor, targetFloorColor, u));

            t += Time.deltaTime;
            yield return null;
        }

        // Swap skybox at "black"
        if (nextHasExposure)
            nextMat.SetFloat("_Exposure", 0f);

        _skyboxMaterialInstance = nextMat;
        RenderSettings.skybox = _skyboxMaterialInstance;

        // Fade in new
        t = 0f;
        while (t < half)
        {
            float u = t / half;

            if (nextHasExposure)
                nextMat.SetFloat("_Exposure", Mathf.Lerp(0f, targetExposure, u));

            t += Time.deltaTime;
            yield return null;
        }

        if (nextHasExposure)
            nextMat.SetFloat("_Exposure", targetExposure);

        _skyboxTransitionRoutine = null;
    }
}