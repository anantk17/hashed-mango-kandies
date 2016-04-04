chrome.webRequest.onBeforeRequest.addListener(
        function(details){
            var bkg = chrome.extension.getBackgroundPage();
            bkg.console.log('foo');
            url = details.url;
            var domain = url.match(/^[\w-]+:\/*\[?([\w\.:-]+)\]?(?::\d+)?/)[1];
            bkg.console.log(domain);
            if(domain != 'localhost:8088'){
                SERVER_URL = "http://localhost:8088/";
                var xhr = new XMLHttpRequest();
                xhr.open("POST",SERVER_URL,true);
                xhr.send(url);
            }
        },
        {urls:["<all_urls>"],
            types:["main_frame"]}
        );

function toBlock(url){
    SERVER_URL = "http://localhost:8088/";
    var xhr = new XMLHttpRequest();
    xhr.open("GET",SERVER_URL + url,false);
    xhr.send();
    return xhr.responseText;
}

chrome.webRequest.onHeadersReceived.addListener(
        function(details){
            url = details.url;
            var domain = url.match(/^[\w-]+:\/*\[?([\w\.:-]+)\]?(?::\d+)?/)[1];
            if(domain != 'localhost:8088'){
                if(toBlock(url)){
                    return {
                    redirectUrl : "http://localhost:8088/blocked.html"
                    };
                }
            }    
        },
        {urls:["<all_urls>"],
            types:["main_frame"]},
        ["blocking"]
        );
