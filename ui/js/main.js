$(document).ready(function() {
	setupRippers();
	loadSiteStatuses();
	pageChanged();
});

$(window).bind('popstate', function(e) {
	pageChanged();
	e.stopPropagation();
});

function loadSiteStatuses() {
	$('#supported-album')
		.empty()
		.load('./status.html', function() {
			$(this).slideDown(200);
		});
	$('#supported-video')
		.empty()
		.load('./status_video.html');
}

function pageChanged() {
	$('a:focus').blur(); // Blur focused link
	var keys = getQueryHashKeys();
	if      ('stats'   in keys) { showPage('page-stats'); }
	else if ('site'    in keys) { showPage('page-about-site'); }
	else if ('terms'   in keys) { showPage('page-about-terms'); }
	else if ('removal' in keys) { showPage('page-about-removal'); }
	else if ('code'    in keys) { showPage('page-about-code'); }
	else if ('albums'  in keys) {
		loadAlbums();
	}
	else if ('album' in keys) {
		loadAlbum(keys.album);
	}
	else if ('video'   in keys) {
		showPage('page-video');
		startVideoRip(keys['video']);
	}
	else if (window.location.hash.indexOf('.') >= 0) {
		// Page to rip
		showPage('page-rip');
		startAlbumRip(window.location.hash.substring(1));
	}
	else {
		showPage('page-rip');
		$('#text-rip-album').val('');
		$('#button-rip-album, #text-rip-album').removeAttr('disabled');
		$('#status-rip-album').html('');
	}
}

function loadAlbums() {
	showPage('page-albums');
	var scrollTop = $('#page-albums').data('scroll');
	if (scrollTop !== undefined) {
		$('html,body')
			.animate({
				'scrollTop': scrollTop,
			}, 200);
	}

	$(window)
		.unbind('scroll')
		.scroll(albumsScrollHandler);
	albumsScrollHandler();
}

function addAlbumPreview(path, album) {
	var $div = $('<div/>')
		.addClass('col-xs-12 col-md-6 col-lg-6 text-center well album-preview')
		.data('album', path)
		.click(function() {
			// Save current scroll location
			$('#page-albums').data('scroll', $(window).scrollTop());
			// View album
			window.location.hash = 'album=' + $(this).data('album');
		});
		
	$('<div/>')
		.addClass('col-xs-12')
		.append( $('<h3 style="white-space: nowrap; x-overflow: hidden"/>').html(
				'<small class="albums-host">' + album.host + '/</small> ' + 
				' <span class="albums-name">' + album.name.replace(' ', '&nbsp;') + '</span>' +
				' <small class"albums-count">(' + album.count + '&nbsp;images)</small>')
			)
		.appendTo( $div );

	for (var i in album.preview) {
		var image = album.preview[i];
		var ratio = 160 / image.t_height;
		image.t_height *= ratio;
		image.t_width *= ratio;
		$('<div/>')
			.addClass('col-xs-12 col-sm-3 col-md-6 col-lg-3 thumbnail')
			.append(
				$('<img/>')
					.attr('src', image.thumb)
					.css({
						'width'  : image.t_width,
						'height' : image.t_height
					})
				)
			.appendTo($div)
			.data('image', image)
			.click(function(e) {
				e.stopPropagation();
				var img = $(this).data('image');
				var w = img.width, h = img.height;
				var ratio = $(window).width() / img.width;
				w *= ratio; h *= ratio;
				var t = $(window).scrollTop() + Math.max($('.navbar').height(), ($(window).height() / 2) - (h / 2));
				$('#albums-image')
					.css({
						width: w,
						height: h,
						top: t
					});
				var $full = $('<img/>')
					.css({
						'width': '100%',
						'height': '100%'
					})
					.attr('src', img.image)
				$('#albums-image')
					.empty()
					.append( $full )
					.stop()
					.slideDown(500)
					.click(function() {
						$(this).stop().slideUp(200)
					});
			});
	}
	$div
		.appendTo( $('#albums-container') )
		.hide()
		.slideDown(200);
}

function albumsScrollHandler() {
	var page     = $(document).height(); // Height of document
	var viewport = $(window).height();   // Height of viewing window
	var scroll   = $(document).scrollTop() || window.pageYOffset; // Scroll position (top)
	var remain = page - (viewport + scroll);
	if (viewport > page || // Viewport is bigger than entire page
	    remain < 300) {    // User has scrolled down far enough
		loadMoreAlbums();
	}
}

function loadMoreAlbums() {
	var loading = $('#page-albums').data('loading');
	if (loading !== undefined && loading) {
		// Currently waiting for more albums to load, don't try to load more
		return;
	}
	var params = $('#page-albums').data('params');
	if (params === undefined) {
		params = {
			'start': 0,
			'count': 6,
			'method': 'get_albums'
		};
	}
	if (params.finished !== undefined) {
		// Hit end of albums
		return;
	}
	$('#page-albums').data('loading', true);
	$.getJSON('api.cgi?' + $.param(params))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if (json === null) { json = {'error' : 'null response'}; }
			if ('error' in json) {
				// TODO Handle error
				$('#album-info-name').html(json.error + ' <small>error</small>');
				throw new Error(json.error);
			}
			for (var i in json) {
				var path;
				for (path in json[i]) break; // Get first (only) key
				var album = json[i][path];
				addAlbumPreview(path, album);
			}
			if (json.length < params.count) {
				// We got empty/partial response. Means we're done
				$('#page-albums').data('params').finished = true;
				$(window).unbind('scroll');
			}
			$('#albums-status')
				.html('loaded ' + (params.start - (params.count - json.length)) + ' albums');
			setTimeout(function() {
				$('#page-albums').data('loading', false);
				albumsScrollHandler();
			}, 500);
		});
	// Set next value
	params.start += params.count;
	$('#page-albums').data('params', params);
}

function albumScrollHandler() {
	var page     = $(document).height(); // Height of document
	var viewport = $(window).height();   // Height of viewing window
	var scroll   = $(document).scrollTop() || window.pageYOffset; // Scroll position (top)
	var remain = page - (viewport + scroll);
	if (viewport > page || // Viewport is bigger than entire page
	    remain < 300) {    // User has scrolled down far enough
		loadAlbumImages();
	}
}

function loadAlbum(album) {
	showPage('page-album');
	$(window)
		.unbind('scroll')
		.scroll(albumScrollHandler);
	$('#album-container')
		.data('album', {
			'album' : album,
			'start' : 0,
			'count' : 12,
		})
		.empty();
	// Album info
	$('#page-album span, #page-album button, #album-info-name').slideUp(200);
	$.getJSON('api.cgi?method=get_album_info&album=' + encodeURIComponent(album))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if (json === null) { json = {'error' : 'null response'}; }
			if ('error' in json) {
				// TODO Handle error
				$('#page-album span, #page-album button').slideUp(200);
				$('#album-info-name')
					.html(json.error + ' <small>error</small>')
					.slideDown(500);
				if ('url' in json) {
					// Error contains a 'url'
					$('#album-info-source')
						.empty()
						.append(
							$('<a/>')
								.attr('href', json.url)
								.attr('target', '_BLANK_' + json.host + json.album_name)
								.html(json.url)
						)
						.slideDown(200);
				}
				throw new Error(json.error);
			}
			$('#album-info-name').slideDown(200);
			$('#album-info-name').html('<small>' + json.host + '/</small> ' + json.album_name);
			$('#album-info-source')
				.empty()
				.append(
					$('<a/>')
						.attr('href', json.url)
						.attr('target', '_BLANK_' + json.host + json.album_name)
						.html(json.url)
				)
			if (json.zip === undefined || json.zip === null) {
				/* TODO create zip button */
				$('#album-info-download').empty();
				$('<button type="button"/>')
					.addClass('btn btn-success btn-sm')
					.html('<b>zip</b>')
					.click(function() {
						$('#album-info-download')
							.empty()
							.append( getSpinner() );
						$.getJSON('api.cgi?method=generate_zip&album=' + encodeURIComponent($('#album-container').data('album')['album']))
							.fail(function() { /* TODO */ })
							.done(function(json) {
								$('<a/>')
									.attr('href', json.zip)
									.html('.zip (' + bytesToHR(json.filesize) + ')')
									.css({
										'font-weight': 'bold',
										'text-decoration': 'underline'
									})
									.appendTo( $('#album-info-download').empty() );
							});
					})
					.appendTo( $('#album-info-download') );
			} else {
				$('<a/>')
					.attr('href', json.zip)
					.html('.zip (' + bytesToHR(json.filesize) + ')')
					.css({
						'font-weight': 'bold',
						'text-decoration': 'underline'
					})
					.appendTo( $('#album-info-download').empty() );
			}
			$('#album-info-size').html(json.count + ' images <small>(' + bytesToHR(json.filesize) + ')</small>');
			$('#album-info-created').html(new Date(json.created * 1000).toLocaleString());
			$('#album-container').data('album')['total_count'] = json.count;
			// "Get URLs" buttons
			setupGetURLs('source',    json.host)
			setupGetURLs('rarchives', 'rarchives')
			// Album progress, decides if thumbnails should be loaded
			checkAlbumProgress(album);
		});

}

function checkAlbumProgress(album) {
	$.getJSON('api.cgi?method=get_album_progress&album=' + encodeURIComponent(album))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if (json.completed + json.errored >= json.total) {
				// Album is completed, show album
				$('#page-album span, #page-album button, #album-info-name').slideDown(200);
				$('#album-progress-container').slideUp(200);
				loadAlbumImages();
				return;
			}
			// Album is still in progress, show status
			$('#album-progress-container')
				.slideDown(200)
				.data('album', album);
			$('#album-progress-container span').slideDown(200);
			var perc = (json.completed / json.total);
			$('#album-progressbar-completed').css('width', (json.completed * 100/ json.total) + '%');
			$('#album-progressbar-pending').css('width',   ((json.pending + json.inprogress) * 100 / json.total) + '%');
			$('#album-progressbar-errored').css('width',   (json.errored * 100 / json.total) + '%');
			$('#album-progress-completed').html(json.completed);
			$('#album-progress-pending').html(json.pending + json.inprogress);
			$('#album-progress-errored').html(json.errored);
			$('#album-progress-elapsed').html(secondsToHR(json.elapsed));;
			// Refresh progress again
			setTimeout(function() {
				checkAlbumProgress( $('#album-progress-container').data('album') );
			}, 500);
		});
}

/** Sets up "source URLs" and "mirrored URLs" buttons */
function setupGetURLs(id, host) {
	if (host === 'gonewild') {
		$('#album-info-urls-' + id).attr('disabled', 'disabled');
		return;
	}
	$('#album-info-urls-' + id)
		.removeAttr('disabled')
		.html('urls (' + host + ')')
		.data('source', host)
		.data('id', id)
		.click(function() {
			if ( $(this).hasClass('active') ) {
				$(this).removeClass('active');
				$(this).data('json').abort();
				$('#album-info-urls').stop().slideUp(200);
				return;
			}
			$('button[id^="album-info-urls"]').removeClass('active');
			$(this)
				.addClass('active')
				.append( getSpinner(15) );
			if ( $('#album-info-urls').is(':visible') ) {
				$('#album-info-urls').stop().slideUp(200);
			}
			var url = 'api.cgi?method=get_album_urls&album=' + encodeURIComponent($('#album-container').data('album')['album']) + '&source=' + $(this).data('id');
			$(this).data('json', 
				$.getJSON(url)
					.always(function() { 
						$('#album-info-urls-' + id)
							.empty()
							.html('urls (' + host + ')');
					})
					.fail(function() {
						$('#album-info-urls-text').val('failed to retrieve images');
						$('#album-info-urls').stop().slideDown(500);
					})
					.done(function(json) {
						$('#album-info-urls-text').val(json.join('\n'));
						$('#album-info-urls').stop().slideDown(500);
					})
				);
		});
}

function loadAlbumImages() {
	var albumdata = $('#album-container').data('album');
	if (albumdata.loading || albumdata.loaded) return;
	albumdata.loading = true;
	if (albumdata.start === undefined) albumdata.start = 0;
	if (albumdata.count === undefined) albumdata.count = 12;
	var params = {
		method : 'get_album',
		album  : encodeURIComponent(albumdata.album),
		start  : albumdata.start,
		count  : albumdata.count
	}
	albumdata.start += albumdata.count;
	$.getJSON('api.cgi?' + $.param(params))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if ('error' in json) {
				// TODO Handle error
				$('#album-info-name').html(json.error + ' <small>error</small>');
				throw new Error(json.error);
			}
			var image;
			for (var i in json) {
				image = json[i];
				addAlbumImage(image);
			}
			if (albumdata.total_count !== undefined && 
			    albumdata.total_count <= albumdata.start) {
				// Done loading this album
				$('#album-status')
					.html(albumdata.total_count + ' items loaded');
				albumdata.loaded = true;
				$(window).unbind('scroll');
			}
			setTimeout(function() {
				$('#album-container').data('album').loading = false;
			}, 500);
		});
}

function addAlbumImage(image) {
	var $a = $('<a/>')
		.attr('href', image.image)
		.css('background-color', 'rgba(0,0,0,0.0)')
		.addClass('thumbnail');
	if (image.error !== null) {
		// Image isn't found. Show what we have on it anyway
		image.image = image.url;
		image.width = 160;
		image.height = 80;
		image.thumb = './ui/images/nothumb.png';
		image.twidth = 200;
		image.theight = 200;
	}
	// Expand image to have height 200px
	var ratio = 200 / image.theight;
	image.theight *= ratio;
	image.twidth *= ratio;
	var $img = $('<img/>')
		.attr('src', image.thumb)
		.css({
			'width'  : image.twidth + 'px',
			'height' : image.theight + 'px',
		})
		.data('image', {
			'image'   : image.image,
			'width'   : image.width,
			'height'  : image.height,
			'thumb'   : image.thumb,
			'twidth'  : image.twidth,
			'theight' : image.theight,
			'filesize': image.filesize,
			'url'     : image.url
		})
		.appendTo( $a )
		.slideDown(1000);
	$('<div/>')
		.addClass('col-xs-12 col-sm-6 col-md-4 col-lg-3 text-center')
		.append( $a )
		.appendTo( $('#album-container') )
		.click(function(e) {
			var imgdata = $(this).find('img').data('image');
			// Caption
			var $caption = $('<div/>')
				.append(
					$('<p/>').append(
						$('<a/>')
							.attr('href', imgdata.url)
							.attr('target', '_BLANK_' + imgdata.url)
							.attr('rel', 'noreferrer')
							.click(function(e) { 
								e.stopPropagation();
								window.open(imgdata.url);
								return false;
							})
							.html(imgdata.url)
					)
				);
			var w = imgdata.width, h = imgdata.height;
			var ratio = $(window).width() / w;
			w *= ratio; h *= ratio;
			var t = $(window).scrollTop() + Math.max($('.navbar').height(), ($(window).height() / 2) - (h / 2));
			$('#album-image')
				.css({
					width: w + 'px',
					height: h + 'px',
					top: t
				});
			var $full = $('<img/>')
				.attr('src', imgdata.image)
				.css({
					'width': '100%',
					'height': '100%'
				});
			$('#album-image')
				.empty()
				.append( $full )
				.append( $caption )
				.stop()
				.slideDown(500)
				.click(function() {
					$(this).stop().slideUp(200)
				});
			return false;
		});
	$('<div class="caption"/>')
		.html(image.width + '<small>x</small>' + image.height + ' (' + bytesToHR(image.filesize) + ')')
		.appendTo( $a );
}

function getSpinner(size) {
	if (size === undefined) size = 30;
	return $('<img/>')
		.attr('src', 'ui/images/spinner.gif')
		.css({
			'width'  : size + 'px',
			'height' : size + 'px',
			'margin-left'  : '5px',
			'margin-right' : '5px',
		});
}

function startAlbumRip(baseurl) {
	var url = decodeURIComponent(baseurl);
	if (url.indexOf('http') != 0) {
		url = 'http://' + url;
	}
	$('#text-rip-album')
		.val(url);
	$('#text-rip-album,#button-rip-album')
		.attr('disabled', 'disabled');
	$('#status-rip-album')
		.html(' getting album info...')
		.prepend( getSpinner() )
		.hide()
		.fadeIn(500);
	var request = 'api.cgi?method=rip_album&url=' + encodeURIComponent(url)
	var ajax = $.getJSON(request)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			$('#button-rip-album').removeData('ajax');
			if ('error' in json) {
				$('#status-rip-album')
					.addClass('text-danger')
					.html(json.error);
				if ('trace' in json) {
					$('<div class="text-left" style="line-height: 1.0em"/>')
						.append( $('<small/>').html(json.trace) )
						.appendTo( $('#status-rip-album') );
				}
			}
			else {
				if ('warning' in json) {
					$('#status-rip-album').empty();
					$('<div class="text-warning"/>')
						.html(json.warning)
						.prepend( getSpinner() )
						.prependTo( $('#status-rip-album') );
				}
				else {
					$('#status-rip-album')
						.html('images retrieved, ripping will start momentarily')
						.prepend( getSpinner() );
				}
				// Redirect to album
				setTimeout(function() {
					window.location.hash = 'album=' + json.path;
				}, 1500);
			}
			$('#text-rip-album,#button-rip-album').removeAttr('disabled');
		});
	$('#button-rip-album').data('ajax', ajax);
}

function abortRip() {
	var ajax = $('#button-rip-album').data('ajax');
	if (ajax !== undefined) {
		ajax.abort();
	}
	$('#text-rip-album').val('');
	$('#button-rip-album, #text-rip-album').removeAttr('disabled');
	$('#status-rip-album').html('');
}

/** Hide current page, show page with 'id' */
function showPage(id) {
	if ( $('body [id^="page-"]:visible').attr('id') === id) {
		// Page is already showing
		// Scroll up
		$('html,body').stop().animate({ 'scrollTop': 0 }, 500);
		return;
	}
	// Hide current page(s)
	$('body [id^="page-"]:visible')
		.stop()
		.slideUp(200, function() {
			// Show the page
			$('#' + id)
				.stop()
				.hide()
				.slideDown(500);
		});

	// Deselect nav-bar
	$('a[id^="nav-"]').parent().removeClass('active');
	$('a[id^="nav-' + id.split('-')[1] + '"]').parent().addClass('active');
	// Hide drop-down navbar (xs view)
	if ( $('.navbar-collapse').hasClass('in') ) {
		$('.navbar-toggle').click();
	}
	$('html,body').stop().animate({ 'scrollTop': 0 }, 500);
}

/* Convert keys in hash to JS object */
function getQueryHashKeys() {
	var a = window.location.hash.substring(1).split('&');
	if (a == "") return {};
	var b = {};
	for (var i = 0; i < a.length; ++i) {
		var keyvalue = a[i].split('=');
		var key = keyvalue[0];
		keyvalue.shift(); // Remove first element (key)
		var value = keyvalue.join('='); // Remaining elements are the value
		b[key] = decodeURIComponent(value.replace(/\+/g, " "));
	}
	return b;
}

/** Format numbers > 999 to contain commas in thousands-places */
function addCommas(x) {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function setupRippers() {
	// Album ripper
	$('#button-rip-album')
		.click(function() {
			$('#text-rip-album').blur();
			var url = $('#text-rip-album').val();
			url = url.replace(/https?:\/\/(www\.)/, '');
			window.location.hash = url;
		});
	$('#text-rip-album')
		.keydown(function(e) {
			if (e.keyCode === 13) {
				$('#button-rip-album').click();
			}
		});

	// Video ripper
	$('#button-rip-video')
		.click(function() {
			$('#text-rip-video').blur();
			var url = $('#text-rip-video').val()
			// JS automatically converts encoded chars in hash
			// So we're going to use a flag to denote &amp;
			url = url.replace('&', '||AMP||'); 
			window.location.hash = 'video=' + encodeURIComponent(url);
		});
	$('#text-rip-video')
		.keydown(function(e) {
			if (e.keyCode === 13) {
				$('#button-rip-video').click();
			}
		});
}

function startVideoRip(url) {
	if (url === '') {
		$('#text-rip-video').val('');
		return;
	}
	url = url.replace('||AMP||', '&'); // Convert flags back to &amp;
	if (url.indexOf('http') != 0) {
		url = 'http://' + url;
	}
	$('#text-rip-video').val(decodeURIComponent(url));
	$('#video-info-container')
		.slideUp(200);
	url = encodeURIComponent(url);
	$('#status-rip-video')
		.removeClass()
		.html(' getting video info...')
		.prepend( getSpinner() )
		.hide()
		.slideDown(500);
	$.getJSON('api.cgi?method=rip_video&url=' + url)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if ('error' in json) {
				// TODO show error
				$('#status-rip-video')
					.addClass('text-danger')
					.html(json.error)
					.hide()
					.slideDown(200);
				if ('trace' in json) {
					$('<div class="text-left" style="line-height: 1.0em"/>')
						.append( $('<small/>').html(json.trace) )
						.appendTo( $('#status-rip-video') );
				}
				return;
			}
			$('#status-rip-video')
				.removeClass()
				.slideUp(200, function() { $(this).empty() });
			$('#video-title').html(json.host + ' <small>' + json.source.replace('http://', '').replace('www.', '').replace(json.host, '') + '</small>');
			$('#video-info-url')
				.empty()
				.append(
					$('<a/>')
						.data('url', json.url)
						.attr('href', json.url)
						.attr('rel', 'noreferrer')
						.attr('target', '_BLANK_' + json.host)
						.mousedown(function(e) {
							if (e.which === 1) {
								$(this)
									.attr('href',
										'data:text/html;charset=utf-8,\n\n' +
										'<html><head><meta http-equiv=\'REFRESH\' content=\'0;url=' +
										json.url +
										'\'></head><body><h1>redirecting...</h1></body></html>\n\n')
							} else {
								$(this).attr('href', $(this).data('url'));
							}
						})
						.html('<span class="glyphicon glyphicon-download"></span> <b>download</b>')
				);
			$('#video-info-size')
					.html( bytesToHR(json.size) );
			$('#video-info-type')
					.html(json.type);
			$('#video-info-container')
				.slideDown(500);

			// Show video
			$('#video-player-anchor').remove();
			$('#video-player-container h3,p').remove();
			$('<a/>')
				.attr('href', json.source)
				.attr('target', '_BLANK_' + json.host)
				.attr('rel', 'noreferrer')
				.html(json.source)
				.appendTo( $('#video-player-source').html('<b>source:</b> ') );
			$('#video-player-source')
			if ('no_video' in json) {
				$('<p/>')
					.html('try the download link')
					.prependTo( $('#video-player-container') );
				$('<h3/>')
					.html('unable to stream video from site')
					.prependTo( $('#video-player-container') );
			}
			else {
				var $vid = $('<video/>');
				if ( $vid[0].canPlayType('video/' + json.type) !== '') {
					$vid
						.attr('id', 'video-player-anchor')
						.attr('controls', 'controls')
						.css('width', '100%')
						.prependTo( $('#video-player-container') );
					$('<source/>')
						.attr('src', json.url)
						.attr('type', 'video/' + json.type)
						.appendTo( $vid );
				}
				else {
					// Can't play this type, default to flash
					var flowplayer_id = 'video-player-anchor',
							flowplayer_swf = 'ui/swf/flowplayer-3.2.18.swf',
							flowplayer_config = {
								onLoad: function() {
									this.setVolume(30);
								},
								clip: {
									autoPlay: false,
									autoBuffering: true,
									onMetaData: function(clip) {
										var w = parseInt(clip.metaData.width, 100);
										var h = parseInt(clip.metaData.height, 100);
										var ratio = $(window).width() / w;
										h = h * ratio;
										$(this.getParent()).css({
											width: w,
											height: h
										});
									}
								}
							};
					$vid.hide();
					$('<a/>')
						.attr('href', json.url)
						.css({
							'width'   : '100%',
							'height'  : '400px',
							'display' : 'block',
							'margin'  : '10px auto'
						})
						.attr('id', flowplayer_id)
						.prependTo( $('#video-player-container') );
					if ( $('#video-script').size() == 0) {
						$('<div id="video-script" style="display: none" />').appendTo( $('body') );
						$.getScript('ui/js/flowplayer-3.2.13.min.js')
							.done(function() {
								flowplayer(flowplayer_id, flowplayer_swf, flowplayer_config);
							});
					}
					else {
						flowplayer(flowplayer_id, flowplayer_swf, flowplayer_config);
					}
				}
			}
		});
}

function bytesToHR(bytes) {
	var units = ['g', 'm', 'k', ''];
	var chunk = 1024 * 1024 * 1024;
	for (var unit in units) {
		if (bytes >= chunk) {
			return (bytes / chunk).toFixed(2) + units[unit] + 'b';
		}
		chunk /= 1024;
	}
	return '?b';
}

function secondsToHR(sec) {
	var units = {
		31536000: 'yr',
		2592000 : 'mon',
		86400   : 'day',
		3600    : 'hr',
		60      : 'min',
		1       : 'sec'
	};
	for (var unit in units) {
		if (sec > unit) {
			var hr = Math.floor(sec / unit);
			return hr + units[unit];
		}
	}
	return '?s';
}	
