// Copyright (c) 2020, Eli2
// SPDX-License-Identifier: AGPL-3.0-or-later

const searchBox = document.getElementById('search-box');

searchBox.removeAttribute('disabled');
searchBox.placeholder = 'Search ...';

const searchScript = document.getElementById('search-script');

// Load the CSS
const cssPath = searchScript.src.slice(0, -3) + '.css';
const cssEl = document.createElement('link');
cssEl.setAttribute('rel', 'stylesheet');
cssEl.setAttribute('type', 'text/css');
cssEl.setAttribute('href', cssPath);
document.head.appendChild(cssEl);

// Wrap the Input textbox
const searchBoxWrap = document.createElement('div');
searchBoxWrap.id = 'search-wrap'
searchBox.replaceWith(searchBoxWrap);
searchBoxWrap.appendChild(searchBox);


let g_searchResultEl;


const g_seaarch = trivialSearchEngine()


searchBox.onfocus = (ev)=>{
	if(!g_searchResultEl) {
		g_searchResultEl = document.createElement('div');
		g_searchResultEl.classList.add('search-results');
		searchBox.insertAdjacentElement('afterend', g_searchResultEl);

		g_seaarch.load();
	}
	g_searchResultEl.classList.remove('hidden');	
};

searchBox.onblur = (ev)=>{
	g_searchResultEl.classList.add('hidden');
}

searchBox.oninput = (ev)=>{

	const createEl = (parent, tag)=>{
		const el = document.createElement(tag)
		parent.appendChild(el);
		return el;
	}
	
	const results = g_seaarch.search(searchBox.value);

	const frag = new DocumentFragment();
	const ul = createEl(frag, 'ul');
	for(const result of results) {
		const mod = result[0];
		const word = result[1][0];
		
		const li = createEl(ul, 'li');
		createEl(li, 'p').innerText = mod.name;
		createEl(li, 'p').innerText = mod.creator;
		createEl(li, 'p').innerText = mod.description;
	}
	g_searchResultEl.innerText = '';
	g_searchResultEl.appendChild(frag);
}


function trivialSearchEngine() {
	let mods;
	let words;

	return {
		'load': ()=>{
			// TODO proper relative URL
			fetch('/search-data.json')
			.then(response => response.json())
			.then(data => {
				mods = data.mods;
				words = data.words;
			})
			.catch(error => console.error(error))
		},
		'search': (query)=>{
			if(!query) {
				return [];
			}

			query = query.toLowerCase();

			result = []
			for(word of words) {
				if(word[0].startsWith(query)) {
					result.push(word);
				}
			}
			result.sort((a, b) => {
				return a[1] - b[1];
				//return a.last_nom.localeCompare(b.last_nom)
			});

			const map = new Map();
			for(r of result) {
				map.set(r[2], r);
			}
			
			const argh = []
			map.forEach((value, key, map)=>{
				argh.push([mods[key], value]);
			});

			return argh;
		}
	}   
}

