console.log("hello.js loaded");
document.title = "HELLO_JS_LOADED";

const p = document.createElement("p");
p.style.color = "cyan";
p.textContent = "external js works";
document.body.appendChild(p);