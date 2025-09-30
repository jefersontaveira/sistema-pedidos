// static/js/admin_panel.js

document.addEventListener('DOMContentLoaded', function() {

    // --- SELEÇÃO DE ELEMENTOS GLOBAIS ---
    const menuItems = document.querySelectorAll('.sidebar-menu .menu-item');
    const views = document.querySelectorAll('.main-content .view');
    const lojaId = document.body.dataset.lojaId;
    const mainContent = document.querySelector('.main-content');

    const modalDetalhes = document.getElementById('modal-detalhes-pedido');
    const btnFecharDetalhes = document.getElementById('btn-fechar-detalhes');
    const btnImprimir = document.getElementById('btn-imprimir-pedido');

    // --- Eventos para fechar e imprimir o modal de detalhes ---
    if (btnFecharDetalhes) {
        btnFecharDetalhes.addEventListener('click', () => modalDetalhes.classList.remove('active'));
    }
    if (modalDetalhes) {
        modalDetalhes.addEventListener('click', (event) => {
            if(event.target === modalDetalhes) modalDetalhes.classList.remove('active');
        });
    }
    if (btnImprimir) {
        btnImprimir.addEventListener('click', () => window.print());
    }

    // =================================================================
    // == LÓGICA DE NAVEGAÇÃO E ESTADO (MEMÓRIA DE PÁGINA) ==
    // =================================================================

    function ativarView(targetId) {
        const targetView = document.getElementById(targetId);
        const targetMenuItem = document.querySelector(`.menu-item[data-target="${targetId}"]`);
        menuItems.forEach(i => i.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        if (targetView && targetMenuItem) {
            targetView.classList.add('active');
            targetMenuItem.classList.add('active');
        }
        if (targetId === 'view-dashboard') {
            fetchDashboardData();
        }
    }

    menuItems.forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            const targetId = this.dataset.target;
            window.location.hash = targetId;
            ativarView(targetId);
        });
    });

    const hashInicial = window.location.hash.substring(1);
    if (hashInicial && document.getElementById(hashInicial)) {
        ativarView(hashInicial);
    } else {
        ativarView('view-dashboard');
        fetchDashboardData();
    }

    // =================================================================
    // == LÓGICA DO WEBSOCKET (DESATIVADA TEMPORARIAMENTE) ==
    // =================================================================
    /*
    if (lojaId) {
        const notificationSound = new Audio('/static/sounds/notification.mp3');
        const socketProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const socketURL = `${socketProtocol}${window.location.host}/ws/painel/${lojaId}/`;
        const socket = new WebSocket(socketURL);
        socket.onopen = function(e) { console.log('Painel Admin: Conexão WebSocket estabelecida!'); };
        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'novo_pedido') {
                console.log('Novo pedido recebido!', data.message);
                notificationSound.play().catch(error => console.error("Erro ao tocar som:", error));
                adicionarCardDePedido(data.message);
            }
        };
        socket.onclose = function(e) { console.error('Painel Admin: Conexão WebSocket fechada. Recarregando em 5s...'); setTimeout(() => window.location.reload(), 5000); };
        socket.onerror = function(err) { console.error('Painel Admin: Erro no WebSocket:', err); };
    }
    function adicionarCardDePedido(pedido) {
        const container = document.querySelector('#coluna-recebidos .cards-container');
        if (!container) return;
        const cardHTML = `<div class="card-pedido" data-pedido-id="${pedido.id}"><h4>Pedido #${pedido.id} <small>${pedido.hora}</small></h4><p><strong>Cliente:</strong> ${pedido.cliente}</p><p><strong>Total:</strong> R$ ${pedido.total}</p></div>`;
        container.insertAdjacentHTML('afterbegin', cardHTML);
    }
    */

    // --- LÓGICA DE DISPONIBILIDADE DO CARDÁPIO ---
    mainContent.addEventListener('change', function(event) {
        // Verifica se o elemento que mudou foi um interruptor de disponibilidade
        if (event.target.classList.contains('toggle-disponibilidade')) {
            const toggle = event.target;
            const isChecked = toggle.checked; // Pega o novo estado (true ou false)

            // Pega as informações do produto a partir da linha da tabela (<tr>)
            const tr = toggle.closest('tr');
            const produtoId = tr.dataset.id;

            // Chama a função que se comunica com o backend
            enviarAtualizacaoDisponibilidade(produtoId, isChecked);
        }
        // Verifica se a mudança foi em um seletor de entregador
        if (event.target.classList.contains('entregador-select')) {
            const select = event.target;
            const entregadorId = select.value;
            const pedidoId = select.closest('.card-pedido').dataset.pedidoId;

            atribuirEntregador(pedidoId, entregadorId);
        }

    });

    // =================================================================
    // == LÓGICA PARA ESCOLHER O ENTREGADOR      ==
    // =================================================================

    async function atribuirEntregador(pedidoId, entregadorId) {
        const payload = {
            pedido_id: pedidoId,
            entregador_id: entregadorId
        };
        try {
            const response = await fetch('/api/atribuir-entregador/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (data.success) {
                console.log(data.message); // Sucesso!
            } else {
                alert('Erro ao atribuir entregador: ' + data.error);
            }
        } catch (error) {
            console.error('Erro de rede:', error);
        }
    }

    // =================================================================
    // == LÓGICA DO CARDÁPIO (DISPONIBILIDADE, ADICIONAR, EDITAR, EXCLUIR) ==
    // =================================================================

    const modal = document.getElementById('modal-adicionar-produto');
    const modalTitulo = modal.querySelector('h2');
    const btnAbrirModal = document.querySelector('#view-cardapio .btn-primario');
    const btnFecharModal = document.getElementById('btn-fechar-modal');
    const btnCancelarModal = document.getElementById('btn-cancelar-modal');
    const formAdicionarProduto = document.getElementById('form-adicionar-produto');
    const tipoProdutoSelect = document.getElementById('tipo-produto');
    const campoNome = document.getElementById('campo-nome');
    const campoPreco = document.getElementById('campo-preco');
    const inputNome = document.getElementById('produto-nome');
    const inputPreco = document.getElementById('produto-preco');

    // --- Delegação de Eventos para todas as ações do Cardápio ---
    mainContent.addEventListener('click', function(event) {
        // Procura por um botão de editar subindo a partir do elemento clicado
        const editButton = event.target.closest('.btn-acao-editar');

        // Procura por um botão de excluir
        const deleteButton = event.target.closest('.btn-acao-excluir');

        // Procura por um botão de ver detalhes (o ícone do olho)
        const detalhesButton = event.target.closest('.btn-ver-detalhes');

        // Procura por um botão de imprimir (o ícone da impressora)
        const imprimirButton = event.target.closest('.btn-imprimir-card');

        // Procura por um botão de aceitar pedido
        const acceptButton = event.target.closest('.btn-aceitar-pedido');

        // Procura por um botão de prosseguir
        const prosseguirButton = event.target.closest('.btn-prosseguir');

        // Procura por um botão de finalizar
        const finalizarButton = event.target.closest('.btn-finalizar');

        // Procura o botão de X para cancelar o pedido
        const cancelarButton = event.target.closest('.btn-cancelar-pedido');

        // Agora, verificamos qual botão foi de fato clicado

        if (editButton) {
            const tr = editButton.closest('tr');
            const nomeTd = tr.cells[0];
            const precoTd = (tr.cells.length > 3) ? tr.cells[1] : null;
            const produto = { id: tr.dataset.id, tipo: tr.dataset.tipo, nome: nomeTd.textContent, preco: precoTd ? precoTd.textContent.replace('R$ ', '').trim() : '0' };
            abrirModalModoEditar(produto);
        }

        if (deleteButton) {
            const tr = deleteButton.closest('tr');
            const produtoId = tr.dataset.id;
            const nomeProduto = tr.cells[0].textContent;
            if (confirm(`Você tem certeza que deseja excluir o item "${nomeProduto}"?`)) {
                excluirProduto(produtoId, tr);
            }
        }

        if (acceptButton) {
            const card = acceptButton.closest('.card-pedido');
            const pedidoId = card.dataset.pedidoId;
            atualizarStatusPedido(pedidoId, 'em_preparo', card);
        }

        if (detalhesButton) {
            const card = detalhesButton.closest('.card-pedido');
            const pedidoId = card.dataset.pedidoId;
            abrirModalDetalhes(pedidoId);
        }

        if (imprimirButton) {
            const card = imprimirButton.closest('.card-pedido');
            const pedidoId = card.dataset.pedidoId;
            prepararEImprimirPedido(pedidoId);
        }

        if (prosseguirButton) {
            const card = prosseguirButton.closest('.card-pedido');
            const pedidoId = card.dataset.pedidoId;
            // Chama a função para mudar o status para 'pronto'
            atualizarStatusPedido(pedidoId, 'pronto', card);
        }

        if (finalizarButton) {
            const card = finalizarButton.closest('.card-pedido');
            const pedidoId = card.dataset.pedidoId;

            // Adicionamos uma confirmação para evitar cliques acidentais
            if (confirm('Você tem certeza que deseja finalizar este pedido? Ele será removido do painel.')) {
                // Chama a função para mudar o status para 'entregue'
                atualizarStatusPedido(pedidoId, 'entregue', card);
            }
        }

        if (cancelarButton) {
            const card = cancelarButton.closest('.card-pedido');
            const pedidoId = card.dataset.pedidoId;

            // Mostra a mensagem de confirmação que você pediu
            if (confirm('Você realmente deseja cancelar o pedido?')) {
                // Chama a nossa função já existente com o novo status 'cancelado'
                atualizarStatusPedido(pedidoId, 'cancelado', card);
            }
        }
    });

    // =================================================================
    // == 4.6. LÓGICA DE DRAG-AND-DROP DOS PEDIDOS ==
    // =================================================================

    const colunas = document.querySelectorAll('.cards-container');
    if (colunas.length > 0) {
        colunas.forEach(coluna => {
            new Sortable(coluna, {
                group: 'pedidos', // Permite mover cards entre colunas com o mesmo grupo
                animation: 150,   // Animação suave ao mover
                ghostClass: 'card-fantasma', // Estilo do placeholder do card

                // Função chamada quando um card é solto em uma nova coluna
                onEnd: function (evt) {
                    const cardMovido = evt.item; // O card que foi arrastado
                    const colunaDestino = evt.to; // A coluna onde o card foi solto

                    const pedidoId = cardMovido.dataset.pedidoId;
                    let novoStatus = '';

                    // Adicionamos a verificação para a coluna de 'recebidos'
                    if (colunaDestino.parentElement.id === 'coluna-recebidos') {
                        novoStatus = 'recebido';
                    } else if (colunaDestino.parentElement.id === 'coluna-em-preparo') {
                        novoStatus = 'em_preparo';
                    } else if (colunaDestino.parentElement.id === 'coluna-prontos') {
                        novoStatus = 'pronto';
                    }
                    // (Poderíamos adicionar 'entregue' aqui no futuro)

                    if (novoStatus) {
                        // Reutilizamos a mesma função de API que já tínhamos!
                        atualizarStatusPedido(pedidoId, novoStatus, cardMovido);
                    }
                }
            });
        });
    }

    // --- Funções de API ---
    async function enviarAtualizacaoDisponibilidade(produtoId, disponivel) {
        // 1. Prepara os dados para enviar
        const payload = {
            produto_id: produtoId,
            disponivel: disponivel,
        };


        try {
            // 2. Envia os dados para a API
            const response = await fetch('/api/atualizar-disponibilidade/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            // 3. Verifica se deu certo
            if (data.success) {
                console.log('Sucesso:', data.message);
            } else {
                console.error('Ocorreu um erro ao salvar a alteração: ' + data.error);
                const input = document.querySelector(`tr[data-id='${produtoId}'] .toggle-disponibilidade`);
                if (input) input.checked = !disponivel;
            }
        } catch (error) {
            console.error('Erro de rede:', error);
        }
    }

    async function excluirProduto(produtoId, linhaElemento) {
        const payload = {
            produto_id: produtoId,
        };

        try {
            const response = await fetch('/api/excluir-produto/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (data.success) {
                linhaElemento.remove(); // Remove a linha da tabela
            } else {
                alert('Erro ao excluir produto: ' + data.error);
            }
        } catch (error) {
            console.error('Erro de rede:', error);
            alert('Erro de conexão ao tentar excluir o produto.');
        }
    }

    function abrirModalModoAdicionar() {
        formAdicionarProduto.removeAttribute('data-editing-id');
        modalTitulo.textContent = 'Adicionar Novo Produto';
        tipoProdutoSelect.disabled = false; modal.classList.add('active');
        }

    function abrirModalModoEditar(produto) {
        formAdicionarProduto.dataset.editingId = produto.id;
        formAdicionarProduto.dataset.editingTipo = produto.tipo;
        modalTitulo.textContent = `Editar Produto: ${produto.nome}`;
        tipoProdutoSelect.value = produto.tipo;
        tipoProdutoSelect.disabled = true;
        tipoProdutoSelect.dispatchEvent(new Event('change'));
        inputNome.value = produto.nome;
        inputPreco.value = produto.preco.replace('.', ',');
        modal.classList.add('active');
    }

    function fecharModal() {
        modal.classList.remove('active');
        formAdicionarProduto.reset();
        campoNome.style.display = 'none';
        campoPreco.style.display = 'none';
        tipoProdutoSelect.disabled = false;
        formAdicionarProduto.removeAttribute('data-editing-id');
        formAdicionarProduto.removeAttribute('data-editing-tipo');
    }

    if(btnAbrirModal) btnAbrirModal.addEventListener('click', abrirModalModoAdicionar);
    if(btnFecharModal) btnFecharModal.addEventListener('click', fecharModal);
    if(btnCancelarModal) btnCancelarModal.addEventListener('click', fecharModal);
    if(modal) modal.addEventListener('click', function(event) {
        if (event.target === modal) fecharModal();
    });

    if(tipoProdutoSelect) tipoProdutoSelect.addEventListener('change', function() {
        const tipo = this.value;
        campoNome.style.display = 'none';
        campoPreco.style.display = 'none';
        if (tipo === 'tamanho' || tipo === 'adicional') {
            campoNome.style.display = 'block';
            campoPreco.style.display = 'block';
        } else if (tipo === 'sabor') {
            campoNome.style.display = 'block';
        }
    });


    // --------------------------------------------------------------------
    // --------------------------------------------------------------------



    if(formAdicionarProduto) formAdicionarProduto.addEventListener('submit', async function(event) {
        event.preventDefault();
        const editingId = formAdicionarProduto.dataset.editingId;
        const tipo = tipoProdutoSelect.value;
        let url = '/api/adicionar-produto/';
        let payload = { loja_id: lojaId, tipo_produto: tipo, nome: inputNome.value, preco: inputPreco.value || '0' };
        if (editingId) {
            url = '/api/editar-produto/';
            payload.produto_id = editingId;
            }
        try {
            const response = await fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload) });
            const data = await response.json();
            if (data.success) {
                if (editingId) {
                    atualizarLinhaTabela(data.produto, tipo);
                } else {
                    adicionarLinhaTabela(data.produto, tipo);
                }
                fecharModal();
            } else {
                alert('Erro: ' + data.error);
            } } catch (error) {
                console.error('Erro de rede:', error);
                alert('Erro de conexão ao tentar salvar o produto.');
            }
        });

    function adicionarLinhaTabela(produto, tipo) {
        const tabelaBody = document.querySelector(`.tabela-cardapio tbody[data-tipo="${tipo}"]`);
        if(!tabelaBody) {
            window.location.reload();
            return;
        }
        let novaLinhaHTML = `<tr data-id="${produto.id}" data-tipo="${tipo}"><td>${produto.nome}</td>`;
        if (tipo === 'tamanho') {
            novaLinhaHTML += `<td>R$ ${produto.preco_base.replace('.',',')}</td>`;
        } else if (tipo === 'adicional') {
            novaLinhaHTML += `<td>R$ ${produto.preco.replace('.',',')}</td>`;
        }
        novaLinhaHTML += `
            <td>
                <label class="switch"><input type="checkbox" class="toggle-disponibilidade" ${produto.disponivel ? 'checked' : ''}>
                    <span class="slider round"></span>
                </label>
            </td>
            <td>
                <button class="btn-acao-editar">
                    <i class="fas fa-pencil-alt"></i>
                </button>
                <button class="btn-acao-excluir">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        </tr>`;
        tabelaBody.insertAdjacentHTML('beforeend', novaLinhaHTML);
    }

    function atualizarLinhaTabela(produto, tipo) {
        const tabelaBody = document.querySelector(`.tabela-cardapio tbody[data-tipo="${tipo}"]`);
        const linha = tabelaBody.querySelector(
            `tr[data-id='${produto.id}']`);
            if (linha) {
                linha.cells[0].textContent = produto.nome;
                if (tipo === 'tamanho') {
                    linha.cells[1].textContent = `R$ ${produto.preco_base.replace('.',',')}`;
                } else if (tipo === 'adicional') {
                    linha.cells[1].textContent = `R$ ${produto.preco.replace('.',',')}`;
                }
            } }


    /**
     * Busca os dados do dashboard na nossa API.
     */
    async function fetchDashboardData() {
        if (!lojaId) return; // Garante que temos um ID de loja

        try {
            const response = await fetch(`/api/dashboard-data/${lojaId}/`);
            if (!response.ok) {
                throw new Error(`Erro na rede: ${response.statusText}`);
            }
            const data = await response.json();
            popularDashboard(data); // Chama a função para preencher a tela
        } catch (error) {
            console.error("Falha ao buscar dados do dashboard:", error);
            // Aqui poderíamos mostrar uma mensagem de erro na tela
        }
    }

    /*
     * Preenche os elementos do dashboard com os dados recebidos da API.
     */
    function popularDashboard(data) {
        document.getElementById('db-faturamento-diario').textContent = `R$ ${data.faturamento_diario}`;
        document.getElementById('db-ticket-medio').textContent = `R$ ${data.ticket_medio}`;

        if (data.pagamento_mais_usado) {
            const totalPedidos = data.pedidos_count;
            const percentual = totalPedidos > 0 ? ((data.pagamento_mais_usado.count / totalPedidos) * 100).toFixed(0) : 0;
            const nomePagamento = data.pagamento_mais_usado.forma_pagamento.charAt(0).toUpperCase() + data.pagamento_mais_usado.forma_pagamento.slice(1);
            document.getElementById('db-pagamento-label').textContent = `${nomePagamento} ${percentual}%`;
        }

        const listaProdutos = document.getElementById('db-produtos-vendidos');
        listaProdutos.innerHTML = ''; // Limpa a lista de "Carregando..."
        if (data.produtos_mais_vendidos.length > 0) {
            data.produtos_mais_vendidos.forEach(produto => {
                const li = document.createElement('li');
                li.textContent = produto.nome;
                listaProdutos.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Nenhuma venda hoje.';
            listaProdutos.appendChild(li);
        }

        document.getElementById('db-status-aguardando').textContent = data.contagem_status.aguardando;
        document.getElementById('db-status-em-preparo').textContent = data.contagem_status.em_preparo;
        document.getElementById('db-status-pronto').textContent = data.contagem_status.pronto;
    }

    /**
     * Envia uma requisição para a API para mudar o status de um pedido
     * e move o card para a coluna correspondente na tela.
     * @param {string} pedidoId - O ID do pedido a ser atualizado.
     * @param {string} novoStatus - O novo status ('em_preparo', 'pronto', etc.).
     * @param {HTMLElement} cardElemento - O elemento do card a ser movido.
     */

    // Em static/js/admin_panel.js

    async function atualizarStatusPedido(pedidoId, novoStatus, cardElemento) {
        const payload = {
            pedido_id: pedidoId,
            novo_status: novoStatus
        };

        try {
            const response = await fetch('/api/atualizar-status-pedido/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (data.success) {
                console.log(data.message);

                // Se o pedido foi entregue, removemos o card e encerramos.
                if (novoStatus === 'entregue' || novoStatus === 'cancelado') {
                    cardElemento.remove();
                    return;
                }

                // --- INÍCIO DA LÓGICA CORRIGIDA E MELHORADA ---

                const actionsDiv = cardElemento.querySelector('.card-actions-pedido > div:last-child');
                let botaoPrincipal = actionsDiv.querySelector('.btn-acao-principal');

                // Se o botão principal não existir (ex: ao voltar para 'recebido'), cria um.
                if (!botaoPrincipal) {
                    botaoPrincipal = document.createElement('button');
                    botaoPrincipal.className = 'btn-acao-principal';
                    actionsDiv.appendChild(botaoPrincipal);
                }

                // Remove todas as classes de status antigas para "limpar" o botão
                botaoPrincipal.classList.remove('btn-aceitar-pedido', 'btn-prosseguir', 'btn-finalizar');

                // Define o novo texto e a nova classe com base no novo status
                if (novoStatus === 'recebido') {
                    botaoPrincipal.classList.add('btn-aceitar-pedido');
                    botaoPrincipal.textContent = 'Aceitar Pedido';
                } else if (novoStatus === 'em_preparo') {
                    botaoPrincipal.classList.add('btn-prosseguir');
                    botaoPrincipal.textContent = 'Prosseguir';
                } else if (novoStatus === 'pronto') {
                    botaoPrincipal.classList.add('btn-finalizar');
                    botaoPrincipal.textContent = 'Finalizar';
                }

                // --- FIM DA LÓGICA CORRIGIDA ---

                // Move o card para a coluna correta
                const mapaColunas = {
                    'recebido': 'coluna-recebidos',
                    'em_preparo': 'coluna-em-preparo',
                    'pronto': 'coluna-prontos',
                };

                const idColunaDestino = mapaColunas[novoStatus];
                if (idColunaDestino) {
                    const colunaDestino = document.querySelector(`#${idColunaDestino} .cards-container`);
                    if (colunaDestino) {
                        const bordas = { 'recebido': '#007bff', 'em_preparo': '#ffc107', 'pronto': '#28a745' };
                        cardElemento.style.borderLeftColor = bordas[novoStatus];
                        colunaDestino.appendChild(cardElemento);
                    }
                }
            } else {
                alert('Erro ao atualizar status: ' + data.error);
            }
        } catch (error) {
            console.error('Erro de rede:', error);
            alert('Erro de conexão ao tentar atualizar o status do pedido.');
        }
    }

    // --- Eventos para fechar e imprimir o modal de detalhes ---
    if (btnFecharDetalhes) {
        btnFecharDetalhes.addEventListener('click', () => modalDetalhes.classList.remove('active'));
    }
    if (modalDetalhes) {
        modalDetalhes.addEventListener('click', (event) => {
            if(event.target === modalDetalhes) modalDetalhes.classList.remove('active');
        });
    }
    if (btnImprimir) {
        btnImprimir.addEventListener('click', () => window.print());
    }

    /**
     * Preenche o modal de detalhes com os dados recebidos da API.
     * @param {object} pedido - Os detalhes do pedido.
     */
    function popularModalDetalhes(pedido) {
        document.getElementById('detalhes-id').textContent = pedido.id;
        document.getElementById('detalhes-hora').textContent = pedido.hora;
        document.getElementById('detalhes-cliente-nome').textContent = pedido.cliente_nome;
        document.getElementById('detalhes-cliente-telefone').textContent = pedido.cliente_telefone;
        document.getElementById('detalhes-cliente-endereco').textContent = pedido.cliente_endereco;
        document.getElementById('detalhes-total').textContent = pedido.total;
        document.getElementById('detalhes-pagamento').textContent = pedido.pagamento;

        const itensListaDiv = document.getElementById('detalhes-itens-lista');
        itensListaDiv.innerHTML = ''; // Limpa a lista anterior

        // Itera sobre cada "Item" (cada açaí montado)
        pedido.itens.forEach((item, index) => {
            let itemHtml = `<div class="item-detalhe-pedido"><strong>Item ${index + 1}</strong><ul>`;

            // Itera sobre os produtos dentro daquele item
            item.produtos.forEach(produto => {
                itemHtml += `<li>${produto.nome}</li>`;
            });

            itemHtml += `</ul></div>`;
            itensListaDiv.innerHTML += itemHtml;
        });

        const obsDiv = document.getElementById('detalhes-observacoes');
        if (pedido.observacoes) {
            obsDiv.innerHTML = `<strong>Observações:</strong> ${pedido.observacoes}`;
            obsDiv.style.display = 'block';
        } else {
            obsDiv.style.display = 'none';
        }
    }

    /**
     * Busca os dados do pedido, preenche o modal e o exibe para o usuário.
     * @param {string} pedidoId - O ID do pedido a ser buscado.
     */
    async function abrirModalDetalhes(pedidoId) {
        // Mostra o modal com um estado de "carregando"
        modalDetalhes.classList.add('active');
        document.getElementById('detalhes-id').textContent = pedidoId;
        document.getElementById('detalhes-itens-lista').innerHTML = '<p>Carregando...</p>';

        try {
            const response = await fetch(`/api/detalhes-pedido/${pedidoId}/`);
            const data = await response.json();

            if (data.success) {
                popularModalDetalhes(data.pedido); // Preenche o modal com os dados recebidos
            } else {
                alert('Erro ao buscar detalhes: ' + data.error);
                modalDetalhes.classList.remove('active');
            }
        } catch (error) {
            console.error("Erro de rede ao buscar detalhes:", error);
            alert("Falha de conexão ao buscar detalhes do pedido.");
            modalDetalhes.classList.remove('active');
        }
    }

    /**
     * Busca os dados do pedido, preenche o modal (sem mostrar) e chama a impressão.
     * @param {string} pedidoId - O ID do pedido para impressão.
     */
    async function prepararEImprimirPedido(pedidoId) {
        try {
            const response = await fetch(`/api/detalhes-pedido/${pedidoId}/`);
            const data = await response.json();
            if (data.success) {
                popularModalDetalhes(data.pedido);
                setTimeout(function() {
                    window.print();
                }, 100);
            } else {
                alert('Erro ao preparar impressão: ' + data.error);
            }
        } catch (error) {
            console.error("Erro de rede ao preparar impressão:", error);
            alert("Falha de conexão ao preparar a impressão.");
        }
    }

    // =================================================================
    // == LÓGICA DO FILTRO DE BUSCA DE PEDIDOS ==
    // =================================================================

    const campoBusca = document.getElementById('busca-pedido');

    if (campoBusca) {
        // O evento 'input' é disparado toda vez que o texto no campo muda
        campoBusca.addEventListener('input', function() {
            // Pega o texto digitado e converte para minúsculas para uma busca sem distinção
            const termoBusca = this.value.toLowerCase().trim();

            // Seleciona todos os cards de pedido que estão na tela
            const todosCards = document.querySelectorAll('.card-pedido');

            // Passa por cada card para decidir se ele deve ser mostrado ou escondido
            todosCards.forEach(card => {
                // Coleta todo o texto de dentro do card que pode ser pesquisado
                const textoDoCard = card.textContent.toLowerCase();

                // Verifica se o texto do card inclui o termo digitado
                if (textoDoCard.includes(termoBusca)) {
                    // Se incluir, garante que o card esteja visível
                    card.style.display = 'flex'; // Usamos flex pois o card é um flex container
                } else {
                    // Se não incluir, esconde o card
                    card.style.display = 'none';
                }
            });
        });
    }
    // ================================================================= fim
    // ================================================================= fim

    // =================================================================
    // == LÓGICA PARA REORDENAR CATEGORIAS COM DRAG-AND-DROP ==
    // =================================================================

    const categoriasContainer = document.getElementById('categorias-container');

    if (categoriasContainer) {
        // Inicia o SortableJS no nosso container de categorias
        new Sortable(categoriasContainer, {
            handle: '.handle-drag', // Define que o arraste só começa ao clicar na "alça" (ícone ⠿)
            animation: 150,
            ghostClass: 'sortable-ghost', // Classe de estilo para o placeholder

            // Função que é executada QUANDO você solta uma categoria na nova posição
            onEnd: function (evt) {
                // Pega todos os blocos de categoria na nova ordem em que estão na tela
                const blocos = categoriasContainer.querySelectorAll('.categoria-bloco');

                // Cria uma lista apenas com os IDs, na nova ordem
                const novaOrdemIds = Array.from(blocos).map(bloco => bloco.dataset.categoriaId);

                console.log("Nova ordem de IDs para salvar:", novaOrdemIds);

                // Chama a função que envia a nova ordem para o backend
                salvarNovaOrdemCategorias(novaOrdemIds);
            }
        });
    }

    /**
     * Envia a nova lista de IDs de categoria para a API no backend.
     * @param {Array<string>} ordemIds - Um array com os IDs das categorias na nova ordem.
     */
    async function salvarNovaOrdemCategorias(ordemIds) {
        const payload = {
            ordem_ids: ordemIds
        };

        try {
            const response = await fetch('/api/reordenar-categorias/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (data.success) {
                console.log(data.message); // Sucesso!
            } else {
                alert('Ocorreu um erro ao salvar a nova ordem: ' + data.error);
                // Futuramente, podemos reverter a ordem visualmente aqui se o backend falhar
            }
        } catch (error) {
            console.error('Erro de rede:', error);
        }
    }
    // ================================================================= fim
    // ================================================================= fim

}); // Fim do 'DOMContentLoaded'