  function getElementComputedStyle(elem, prop)
{
  if (typeof elem!="object") elem = document.getElementById(elem);
  
  // external stylesheet for Mozilla, Opera 7+ and Safari 1.3+
  if (document.defaultView && document.defaultView.getComputedStyle)
  {
    if (prop.match(/[A-Z]/)) prop = prop.replace(/([A-Z])/g, "-$1").toLowerCase();
    return document.defaultView.getComputedStyle(elem, "").getPropertyValue(prop);
  }
  
  // external stylesheet for Explorer and Opera 9
  if (elem.currentStyle)
  {
    var i;
    while ((i=prop.indexOf("-"))!=-1) prop = prop.substr(0, i) + prop.substr(i+1,1).toUpperCase() + prop.substr(i+2);
    return elem.currentStyle[prop];
  }
  
  return "";
}
