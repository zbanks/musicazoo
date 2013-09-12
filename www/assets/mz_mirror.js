var player;
function playYoutubeVideo(id, time, updateState) {
    var last_state = -1;
    player = new YT.Player('video', {
        height: '390',
        width: '640',
        events: {
            'onReady': function(ev){
                //ev.target.playVideo(); 
                player.loadVideoById(id, time);
                //ev.target.seekTo(time*1, true);
            },
            'onStateChange': function(ev){
                var state = ev.data;
                switch(ev.data){
                    case -1: // Unstarted
                    break;
                    case 0: // Ended
                    break;
                    case 1: // Playing
                        player.status = "playing";
                        if(last_state != state){
                            updateState(state);
                        }
                    break;
                    case 2: // Paused
                        player.status = "paused";
                        if(last_state != state){
                            updateState(state);
                        }
                    break;
                    case 3: // Buffering

                    break;
                    case 5: // Video Cued

                    break;
                    default: 
                    break;
                }
                last_state = state;
            }
        }
    });
    return player;
}


function musicazooLoaded(mz){
    console.log("Musicazoo: ", mz);
    var MirrorView = Backbone.View.extend({
        act_template: Handlebars.compile("{{{ html }}}"),
        update_time: function(remote){
            if(this.player && this.player.getCurrentTime){
                var remote_time = this.model.get('time');
                var local_time = this.player.getCurrentTime();
                if(Math.abs(remote_time - local_time) > 5){
                    if(remote){
                        this.model.set('time', local_time);
                    }else{
                        this.player.seekTo(remote_time);
                    }
                }
            }
        },
        initialize: function(){
            var self = this;
            this.listenTo(this.model, "change", function(model){
                /* XXX: Can't get change:time to work :( */
                console.log(model.attributes);
                if(this.model.get('type') == 'youtube'){
                    this.update_time(false);
                }
            });
            this.listenTo(this.model, "change:exists", function(model, value, options){
                if(value == false){
                    if(this.player){
                        this.player.destroy();
                        this.player = null;
                        $('.video').html('');
                    }
                }
            });
            this.listenTo(this.model, "change:uid", function(model){
                if(this.player){
                    this.player.destroy();
                }
                $('.video').html('');
                console.log('hello', this.model.get('time'));
                if(this.model.get('type') == 'youtube'){
                    console.log(this.model.attributes);
                    
                    this.player = playYoutubeVideo(this.model.get('vid'), this.model.get('time'), function(state){
                        if(state == 1){
                            model.set('status', 'playing');
                            self.update_time(true);
                        }else if(state == 2){
                            model.set('status', 'paused');
                        }
                    });
                }else{
                    this.player = null;
                }
            });
            this.render();
            return this;
        }
    });

    var cv = new MirrorView({model: mz.get('active'), el: $(".display-area")});
}

