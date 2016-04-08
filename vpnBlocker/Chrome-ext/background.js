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

var SERVER_URL = "http://localhost:8080/";

chrome.webRequest.onBeforeRequest.addListener(
        function(details){
            var bkg = chrome.extension.getBackgroundPage();
            bkg.console.log(details.requestId);
            bkg.console.log('foo');
            url = details.url;
            ///timeStamp = details.timeStamp;
            timeStamp = (new Date()).getTime();
            bkg.console.log(timeStamp);
            requestId = details.requestId;
            var domain = extractDomain(url);
            bkg.console.log(domain);
            if(domain != 'localhost'){
                //SERVER_URL = "http://localhost:8088/";
                var xhr = new XMLHttpRequest();
                var data = new FormData();
                data.append('domain',domain);
                //data.append('timestamp',timeStamp);
                data.append('request_id',requestId);
                data.append('send_time',timeStamp);
                xhr.open("POST",SERVER_URL+'record/',true);
                xhr.send(data);
            }
        },
        {urls:["<all_urls>"],
            types:["main_frame"]}
        );

function toBlock(requestId,rec_time){
    //SERVER_URL = "http://localhost:8088/";
    var xhr = new XMLHttpRequest();
    xhr.open("GET",SERVER_URL + 'query?request_id='+requestId+'&rec_time='+rec_time,false);
    xhr.send();
    return parseInt(xhr.responseText);
}

chrome.webRequest.onHeadersReceived.addListener(
        function(details){
            var bkg = chrome.extension.getBackgroundPage();
            bkg.console.log(details.requestId);
            url = details.url;
            requestId = details.requestId;
            //timeStamp = details.timeStamp;
            timeStamp = (new Date()).getTime();
            bkg.console.log(timeStamp);
            ///bkg.console.log(details.statusCode);
            statusCode = details.statusCode;
            var domain = extractDomain(url);
            if(domain != 'localhost' && statusCode== 200){
                //bkg.console.log("Proxy Used" + toBlock(requestId,timeStamp));
                bkg.console.log(statusCode);
                if(toBlock(requestId,timeStamp)){
                    return {
                    redirectUrl : SERVER_URL+"block/"
                    };
                }
            }    
        },
        {urls:["<all_urls>"],
            types:["main_frame"]},
        ["blocking"]
        );
