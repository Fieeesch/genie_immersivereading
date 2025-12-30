using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class DisableScrollOnPress : MonoBehaviour,
    IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
{
    [SerializeField] private ScrollRect scrollRect;
    
    private void Awake()
    {
        if (scrollRect == null)
            scrollRect = GetComponentInParent<ScrollRect>();
    }

    public void OnPointerDown(PointerEventData eventData)
    {
        if (scrollRect != null)
            scrollRect.enabled = false;
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        if (scrollRect != null)
            scrollRect.enabled = true;
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        if (scrollRect != null)
            scrollRect.enabled = true;
    }
}