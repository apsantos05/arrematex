let lotes = [];
let loteAtivo = null;
let historicoLances = [];
let vendasRealizadas = [];

function showTab(t) {
  ['cadastro','leilao','relatorio'].forEach(x => {
    document.getElementById('content-'+x).style.display =
      x===t ? 'block' : 'none';

    document.getElementById('tab-'+x)
      .classList.toggle('active', x===t);
  });

  if(t==='leilao') atualizarSelectLote();
  if(t==='relatorio') atualizarRelatorio();
}

function fmtBRL(v) {
  return 'R$ ' + v.toLocaleString('pt-BR', {
    minimumFractionDigits:2,
    maximumFractionDigits:2
  });
}

function cadastrarLote() {

  const num = parseInt(document.getElementById('f-lote').value);

  const desc = document.getElementById('f-desc')
    .value.trim()
    .toUpperCase();

  const qtd = parseInt(document.getElementById('f-qtd').value);

  const peso = parseInt(document.getElementById('f-peso').value);

  const lance = parseFloat(document.getElementById('f-lance').value);

  const prazo = document.getElementById('f-prazo').value;

  if(!num || !desc || !qtd || !peso || !lance) {

    document.getElementById('msg-cadastro').style.color='#e24b4a';

    document.getElementById('msg-cadastro').textContent =
      'Preencha todos os campos!';

    return;
  }

  lotes.push({
    num,
    desc,
    qtd,
    peso,
    lance,
    prazo,
    status:'aguardando',
    lanceAtual:lance
  });

  renderTabela();
}

/* CONTINUE COLANDO TODO O JAVASCRIPT AQUI */

renderTabela();