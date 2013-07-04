var volume_lockout = false;
setInterval(function(){ volume_lockout = false; }, 500);

// http://www.knockmeout.net/2011/05/dragging-dropping-and-sorting-with.html
//connect items with observableArrays
ko.bindingHandlers.sortableList = {
  init: function(element, valueAccessor) {
      var list = valueAccessor();
      $(element).sortable({
          update: function(event, ui) {
              //retrieve our actual data item
              var item = ui.item.tmplItem().data;
              //figure out its new position
              var position = ko.utils.arrayIndexOf(ui.item.parent().children(), ui.item[0]);
              //remove the item and add it back in the right spot
              if (position >= 0) {
                  list.remove(item);
                  list.splice(position, 0, item);
              }
          }
      });
  }
};

$(document).ready(function(){
    $(".uploadFile").submit(function(){
        $(".queueform");
    });
    

    $("input.addtxt").keyup(function(){
        var query = $(this).val();
        if(query == ""){
            $(".results").html("");
            return;
        }
        var ytrequrl = "http://gdata.youtube.com/feeds/api/videos?v=2&orderby=relevance&alt=jsonc&q=" + encodeURIComponent(query) + "&max-results=5&callback=?"
        $.getJSON(ytrequrl, function(data){
            var list = $("<ol class='suggest'></ol>");
            var i = 0;
            var index = query.indexOf(" ");

            if(index == -1){
                cmd_ = "";
                cmd = query.toLowerCase();
            }else{
                var cmd_ = query.substr(index);
                var cmd = query.substr(0, index).toLowerCase();
            }
            
            var isCmdPrefix = function(prefix){
                if(cmd.length < prefix.length){
                    return cmd == prefix.substr(0, cmd.length);
                }
                if(cmd.length == 0){
                    return false;
                }
                return cmd == prefix
            }

            for(var j = 0; j < window.commands.length && i < 5; j++){
                var c = window.commands[j];
                console.log(c, cmd);

                if(isCmdPrefix(c)){
                    console.log(c, cmd_);
                    list.append($("<a href='/add/" + c + "+" + cmd_ + "'><li><strong>" + c + "</strong>" + cmd_ + "</li></a>"));
                    i++
                }
            }

            for(var j = 0; j < data.data.items.length && j + i < 5; j++){
                var vid = data.data.items[j];
                list.append($("<a href='/add/youtube/" + vid.id + "'><li>" + vid.title + "</li></a>"));
            }
            $(".results").html("").append(list);
        });
        return true;
    });

    $(".queueform").submit(function(){
        if($("input[type=file]").val()){
            return;
        }
        var query = $(".addtxt").val();
        if(!query){
            return false;
        }
        $(".addtxt").val("");
        $.post("/add/" + encodeURIComponent(query),  function(data){
            console.log(data);
            if(!data.success){
                $("div.error").html(data.error).show(300, function(){
                    setTimeout(5000, function(){
                        $("div.error").hide(200);
                    });
                });
            }
            refreshPlaylist();
            $(".addtxt").val("");
        });
        return false; // Prevent form submitting
    });

    $("div.vol-slider").slider({
        orientation: "horizontal",
        range: "min",
        min: 0,
        max: 100,
        value: window.volume,
        slide: function(ev, ui) {
            updateSlider(ui.value);
            if(volume_lockout == true)
                return;
            volume_lockout = true;
            console.log(ui.value);
            $.get("/vol/" + ui.value, function(){
                volume_lockout = false;   
            });
        }
    });
    updateSlider(window.volume);
    $(".ui-slider-range").html("<span data-bind='text: mz().volume'></span>");
    
    $("ol.playlist").sortable({
        update: function(ev, ui){
            var ordering = $("ol.playlist li").map(function(i, e){return $(e).attr('id')}).toArray().join(";");
            var url = "/msg?queue_cmd=mv&ordering=" + ordering;
            $.get(url);
        },
        start: function(ev, ui){
            window.no_autorefresh = true;
        },
        stop: function(ev, ui){
            window.no_autorefresh = false;
        }
    });
    console.log(vm);
    ko.applyBindings(vm); 

});

var updateSlider = function(value){
    $("div.vol-slider").slider("option", "value", value);
}


var mz_map = {
    playlist: {
        key: function(data){
            return ko.utils.unwrapObservable(data.id);
        }
    },
    current: {
        key: function(data){
            console.log(data.id);
            return ko.utils.unwrapObservable(data.id);
        }
    },
    observe: ['volume']
};

var MOULES = {
    "youtube" : {"params": "url"}
};

var STATICS = {
    "volume" : {"params": "vol"}
};

BASE_URL = "http://192.168.0.7:9000/";

function ViewModel() { 
    var self = this;
    self.mz = ko.observable(false);
    self.mz.volume = ko.observable(0);
    self.reload = function() {
        deferQuery({"cmd": "queue"}, function(queue_list) {
            if(window.no_autorefresh) return;
            var fetch_module_params = function(q){
                if(MODULES[q.module]){
                    var params = [];
                    var m_params = MODULES[q.module].params;
                    for(var i = 0; i < m_params; i++){
                        deferQuery({"cmd": "get_" + m_params[i]}, function(v){
                            q[m_params[i]] = v;        
                        });
                    }
                    return params;
                }
                console.log("Unknown module: " + q.module);
                return [];
            };
            /*
            var parse_module_results = function(q, qr){
                if(MODULES[q.module]){
                    var qi = {};
                    var m_params = MODULES[q.module].params
                    for(var i = 0; i < m_params; i++){
                        var res = qr.pop();//qr[q.id + "_" + m_params[i]];
                        if(res.success){
                            qi[m_params[i]] = res.result;
                        }else{
                            console.log(res.error);
                        }
                    }
                    return qi;
                }
                console.log("Unknown module: " + q.module);
                return {};
            };
            */

            for(var i = 0; i < queue_list.length; i++){
                fetch_module_params(queue_list[i]);
            }
            runQueries(function(){
                console.log("Loaded queue:");
                console.log(queue_list);
                self.mz(ko.mapping.fromJS(queue_list));
                $("ol.playlist").sortable("refresh");
            });
            /*
            $.post(BASE_URL, qu_query, function(queue_data){
                if(!queue_data.success){
                    console.log(data.error);
                    return;
                }
                var queue_items = [];
                for(var i = 0; i < results.queue.length; i++){
                    queue_items.push(parse_module_results(results.queue[i], queue_data));
                }
            }, 'json');
            */
            //self.mz(ko.mapping.fromJS(data));
            //updateSlider(self.mz().volume()); // Shitty and not ko.js style. FIXME
            //$("ol.playlist").sortable("refresh");
        }, 'json');
    };
};  


vm = new ViewModel();

var refreshPlaylist = function(firstTime){
    vm.reload();
}

refreshPlaylist(true);
// Refresh playlist every 1 seconds
setInterval(refreshPlaylist, 1000);


var _query_queue = [];
var _runquery_timeout;

function deferQuery(data, cb){
    _query_queue.push({"data": data, "cb": cb});
}

function forceQuery(data, cb){
    _query_queue.push({"data": data, "cb": cb});
    runQueries();
}


function runQueries(cb){
    window.clearTimeout(_runquery_timeout);
    if(_query_queue.length){
        var cbs = _.pluck(_query_queue, "cb");
        var datas = _.pluck(_query_queue, "data");
        $.post(BASE_URL, datas, function(resp){
            if(resp.length != cbs.length){ 
                console.error("Did not recieve correct number of responses from server!");
                return;
            }
            for(var i = 0; i < resp.length; i++){
                var r = resp[i];
                if(!r.success){
                    console.log(r.error);
                }else{
                    cbs[i](r.result);
                }
            }
            _runquery_timeout = window.setTimeout(runQueries, 0); // Defer
        }, 'json');
    }else{
        _runquery_timeout = window.setTimeout(runQueries, 50);
    }
    if(cb){
        cb();
    }
}

runQueries();
