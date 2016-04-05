function extractDomain(url){
    var domain;
    if(url.indexOf("://") > -1){
        domain = url.split('/')[2];
    }
    else{
        domain = url.split('/')[0];
    }
    domain = domain.split(':')[0];

    return domain;
}

var SERVER_URL = "http://localhost:8088/";

chrome.webRequest.onBeforeRequest.addListener(
        function(details){
            var bkg = chrome.extension.getBackgroundPage();
            bkg.console.log('foo');
            url = details.url;
            timestamp = details.timeStamp;
            requestId = details.requestId;
            var domain = extractDomain(url);
            bkg.console.log(domain);
            if(domain != 'localhost'){
                //SERVER_URL = "http://localhost:8088/";
                var xhr = new XMLHttpRequest();
                var data = new FormData();
                data.append('domain',domain);
                data.append('timestamp',timeStamp);
                data.append('requestId',requestId);
                xhr.open("POST",data,true);
                xhr.send(data);
            }
        },
        {urls:["<all_urls>"],
            types:["main_frame"]}
        );

function toBlock(domain,timeStamp){
    //SERVER_URL = "http://localhost:8088/";
    var xhr = new XMLHttpRequest();
    xhr.open("GET",SERVER_URL + '?domain='+domain+'&time='+ timeStamp,false);
    xhr.send();
    return xhr.responseText;
}

chrome.webRequest.onHeadersReceived.addListener(
        function(details){
            url = details.url;
            timeStamp = details.timeStamp;
            var domain = extractDomain(url);
            if(domain != 'localhost'){
                if(toBlock(domain,timeStamp)){
                    return {
                    redirectUrl : "http://localhost:8088/blocked"
                    };
                }
            }    
        },
        {urls:["<all_urls>"],
            types:["main_frame"]},
        ["blocking"]
        );
