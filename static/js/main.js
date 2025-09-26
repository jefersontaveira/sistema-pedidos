// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {

    // =====================================================================
    // =================== CONSTANTES
    // =====================================================================

    // CONSTANTES PARA SELECIONAR O ITEM DO PEDIDO
    const itensMenu = document.querySelectorAll('.item-menu');

    // CONSTANTES DO CARRINHO ABRIR E FECHAR
    const iconeCarrinho = document.getElementById('icone-carrinho');
    const sidebarCarrinho = document.getElementById('carrinho-sidebar');
    const overlayCarrinho = document.getElementById('carrinho-overlay');
    const btnFecharCarrinho = document.getElementById('btn-fechar-carrinho');

    // CONSTANTES E VARIÁVEIS PARA ADICIONAR O PEDIDO AO CARRINHO E FAZER OUTRO PEDIDO
    let carrinhoFinal = []; // Guardará a lista de produtos montados
    const itensCarrinhoFinalDiv = document.getElementById('itens-carrinho-final');
    const totalCarrinhoFinalSpan = document.getElementById('total-carrinho-final');
    const carrinhoContadorSpan = document.getElementById('carrinho-contador');

    // CONSTANTE DO ID DA LOJA PARA ENVIAR O PEDIDO
    const lojaId = document.body.dataset.lojaId;
    const lojaWhatsapp = document.body.dataset.lojaWhatsapp;

    // =============================================================== FIM
    // =============================================================== FIM

    // =====================================================================
    // =================== LÓGICA PARA SELECIONAR OS ITENS DO PEDIDO
    // =====================================================================

    // Para cada item do menu, adicionamos um "ouvinte" de clique.
    itensMenu.forEach(item => {
        item.addEventListener('click', function() {
            // Pega a categoria do item clicado a partir do data-attribute da seção.
            const categoriaElemento = this.closest('.categoria-menu');
            const categoriaNome = categoriaElemento.dataset.categoriaNome;

            // REGRA ESPECIAL: Se a categoria for 'Tamanhos', garante seleção única.
            if (categoriaNome.toLowerCase() === 'tamanhos') {
                // Se o tamanho clicado já está selecionado, não faz nada e sai da função.
                if (this.classList.contains('selecionado')) {
                    return;
                }

                // Procura por todos os itens de 'Tamanhos' e remove a seleção deles.
                document.querySelectorAll('.categoria-menu[data-categoria-nome="Tamanhos"] .item-menu').forEach(el => {
                    el.classList.remove('selecionado');
                });
            }

            // Adiciona ou remove a classe 'selecionado' do item que foi clicado.
            // Para 'Tamanhos', ele sempre vai adicionar, pois a lógica acima já limpou os outros.
            // Para as outras categorias, ele vai adicionar se não tiver, e remover se já tiver.
            this.classList.toggle('selecionado');
        });
    });
    // =============================================================== FIM
    // =============================================================== FIM

    // =====================================================================
    // =================== ABRIR E FECHAR MENU
    // =====================================================================

    // Define as funções que fazem a ação de abrir e fechar
    // Elas simplesmente adicionam ou removem a classe CSS 'is-open'
    function abrirCarrinho() {
        if (sidebarCarrinho) sidebarCarrinho.classList.add('is-open');
        if (overlayCarrinho) overlayCarrinho.classList.add('is-open');
    }

    function fecharCarrinho() {
        if (sidebarCarrinho) sidebarCarrinho.classList.remove('is-open');
        if (overlayCarrinho) overlayCarrinho.classList.remove('is-open');
    }

    // Conecta as funções aos cliques nos elementos corretos
    // As verificações 'if (elemento)' garantem que o código não quebre
    if (iconeCarrinho) {
        iconeCarrinho.addEventListener('click', abrirCarrinho);
    }
    if (btnFecharCarrinho) {
        btnFecharCarrinho.addEventListener('click', fecharCarrinho);
    }
    if (overlayCarrinho) {
        overlayCarrinho.addEventListener('click', fecharCarrinho);
    }
    // ================================================================ FIM
    // ================================================================ FIM

    // =====================================================================
    // ====== LÓGICA PARA RENDERIZAR O CARRINHO AO ADICIONAR O PEDIDO
    // =====================================================================

    function renderizarCarrinhoFinal() {
        const itensCarrinhoFinalDiv = document.getElementById('itens-carrinho-final');
        const totalCarrinhoFinalSpan = document.getElementById('total-carrinho-final');
        const carrinhoContadorSpan = document.getElementById('carrinho-contador');

        itensCarrinhoFinalDiv.innerHTML = '';
        let totalGeral = 0;

        if (carrinhoFinal.length === 0) {
            itensCarrinhoFinalDiv.innerHTML = '<p class="aviso-carrinho">Seu carrinho está vazio.</p>';
        } else {
            carrinhoFinal.forEach((item, index) => {
                let subtotalItem = 0;
                let categoriasHtml = '';

                const produtosPorCategoria = new Map();
                item.forEach(produto => {
                    if (!produtosPorCategoria.has(produto.categoriaNome)) {
                        produtosPorCategoria.set(produto.categoriaNome, []);
                    }
                    produtosPorCategoria.get(produto.categoriaNome).push(produto);
                    subtotalItem += produto.preco;
                });

                // Monta o HTML para cada categoria e seus itens, agora com o preço ao lado.
                produtosPorCategoria.forEach((produtos, nomeCategoria) => {
                    categoriasHtml += `<strong>${nomeCategoria}</strong><ul>`;
                    produtos.forEach(produto => {
                        let precoHtml = '';
                        // Só mostra o preço se ele for maior que zero
                        if (produto.preco > 0) {
                            precoHtml = `<span class="item-preco-carrinho">+ R$ ${produto.preco.toFixed(2).replace('.', ',')}</span>`;
                        }
                        categoriasHtml += `<li> ${produto.nome} ${precoHtml}</li>`;
                    });
                    categoriasHtml += `</ul>`;
                });

                const itemDiv = document.createElement('div');
                itemDiv.className = 'item-no-carrinho';
                // O cabeçalho do item agora inclui o subtotal e a lixeira.
                itemDiv.innerHTML = `
                    <div class="item-carrinho-header">
                        <strong>Pedido ${index + 1}</strong>
                        <div class="item-carrinho-actions">
                            <span>R$ ${subtotalItem.toFixed(2).replace('.', ',')}</span>
                            <button class="btn-remover-item" data-index="${index}" title="Remover item">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                    </div>
                    <div class="item-carrinho-body">
                        ${categoriasHtml}
                    </div>
                `;
                    itensCarrinhoFinalDiv.appendChild(itemDiv);
                    totalGeral += subtotalItem;
                });
            }

            // Atualiza o total geral na tela
            totalCarrinhoFinalSpan.textContent = `R$ ${totalGeral.toFixed(2).replace('.', ',')}`;
            // Atualiza o contador no ícone do carrinho no topo da página
            carrinhoContadorSpan.textContent = carrinhoFinal.length;
            salvarCarrinho()
        }

    // ================================================================ FIM
    // ================================================================ FIM

    // =====================================================================
    // LÓGICA PARA CONECTAR O BOTÃO ADICIONAR E MONTAR OUTRO A FUNÇÃO DE RENDERIZAR NO CARRINHO
    // =====================================================================

    // CONSTANTE DO BOTÃO
    const btnFazerOutroPedido = document.getElementById('btn-fazer-outro-pedido');

    // Função para coletar os itens selecionados e retorná-los
    function coletarItensSelecionados() {
        const itensSelecionados = document.querySelectorAll('.item-menu.selecionado');
        if (itensSelecionados.length === 0) {
            return null;
        }

        const itemMontado = [];
        let temTamanho = false;

        itensSelecionados.forEach(item => {
            const produtoInfo = {
                id: item.dataset.produtoId,
                nome: item.dataset.produtoNome,
                preco: parseFloat(item.dataset.produtoPreco),
                categoriaNome: item.closest('.categoria-menu').dataset.categoriaNome
            };
            itemMontado.push(produtoInfo);

            if (produtoInfo.categoriaNome.toLowerCase() === 'tamanhos') {
                temTamanho = true;
            }
        });

        // Validação: só retorna o item se pelo menos um tamanho foi selecionado
        if (!temTamanho) {
            alert('Você precisa selecionar pelo menos um tamanho para montar um pedido.');
            return null;
        }

        return itemMontado;
    }

    // Adiciona o "ouvinte" de evento ao botão
    btnFazerOutroPedido.addEventListener('click', function() {
        const itemParaAdicionar = coletarItensSelecionados();

        if (itemParaAdicionar) {
            // Adiciona o grupo de itens selecionados ao carrinho final
            carrinhoFinal.push(itemParaAdicionar);
            // Redesenha a interface do carrinho
            renderizarCarrinhoFinal();
            // Limpa as seleções da tela para o próximo pedido
            document.querySelectorAll('.item-menu.selecionado').forEach(el => {
                el.classList.remove('selecionado');
            });
        }
    });
    // ================================================================ FIM
    // ================================================================ FIM

    // =================================================================
    // == LÓGICA PARA REMOVER ITEM DO CARRINHO FINAL ==
    // =================================================================

    // Usamos delegação de eventos para "ouvir" cliques na área dos itens do carrinho.
    // Isso garante que mesmo os itens adicionados dinamicamente terão o botão funcional.
    itensCarrinhoFinalDiv.addEventListener('click', function(event) {

        // Verifica se o elemento que foi clicado (ou um de seus pais)
        // é o botão de remover com a classe '.btn-remover-item'.
        const removerButton = event.target.closest('.btn-remover-item');

        // Se o clique não foi em um botão de remover, a função para aqui.
        if (!removerButton) {
            return;
        }

        // Pega o 'index' que guardamos no atributo 'data-index' do botão
        // para sabermos qual item remover da nossa lista.
        const indexParaRemover = parseInt(removerButton.dataset.index, 10);

        // Remove 1 item do nosso array 'carrinhoFinal' na posição encontrada.
        carrinhoFinal.splice(indexParaRemover, 1);

        // Chama a função que já temos para redesenhar o carrinho com a lista atualizada.
        // A numeração dos pedidos ("Pedido 1", "Pedido 2") será recalculada automaticamente.
        renderizarCarrinhoFinal();
    });
    // ================================================================ FIM
    // ================================================================ FIM

        // =================================================================
    // == FUNÇÕES QUE SALVA E CARREGA O CARRINHO NO LOCALSTORAGE DO NAVEGADOR ==
    // =================================================================

    function salvarCarrinho() {
        // É onde será guardado o carrinho para que não se perca ao atualizar
        // a página
        localStorage.setItem('carrinhoDaLoja', JSON.stringify(carrinhoFinal));
    }

    // Carrega os dados do carrinho do localStorage quando a página inicia.
    function carregarCarrinho() {
        // Tenta buscar o texto do carrinho salvo na memória.
        const carrinhoSalvo = localStorage.getItem('carrinhoDaLoja');

        // Se encontrou algo...
        if (carrinhoSalvo) {
            // ...converte o texto de volta para um array de objetos...
            carrinhoFinal = JSON.parse(carrinhoSalvo);
            // ...e chama a função para desenhar o carrinho na tela.
            renderizarCarrinhoFinal();
        }
    }

    // =================================================================
    // == LÓGICA PARA NAVEGAÇÃO DO CHECKOUT ==
    // =================================================================

    // Seleciona os elementos da nova tela
    const telaCheckout = document.getElementById('tela-checkout');
    const btnFinalizarPedido = document.getElementById('btn-finalizar-pedido');
    const btnVoltarCardapio = document.getElementById('btn-voltar-cardapio');
    const checkoutTotalSpan = document.getElementById('checkout-total-valor');
    const btnFinalizarDireto = document.getElementById('btn-finalizar-direto');

    // ================================================================ FIM
    // ================================================================ FIM

    // =================================================================
    // == FUNÇÃO QUE ABRE A TELA DE CHECKOUT ==
    // =================================================================

    function abrirCheckout() {
        // Validação para não prosseguir se o carrinho estiver vazio
        if (carrinhoFinal.length === 0) {
            alert('Seu carrinho está vazio!');
            return;
        }

        // Atualiza o valor total na tela de checkout
        checkoutTotalSpan.textContent = totalCarrinhoFinalSpan.textContent;

        // Fecha a sidebar do carrinho (se estiver aberta) e mostra a tela de checkout
        fecharCarrinho();
        telaCheckout.classList.add('is-open');
    }

        // Conecta a função aos dois botões de "Finalizar Pedido"
    btnFinalizarPedido.addEventListener('click', abrirCheckout);

    btnFinalizarDireto.addEventListener('click', function() {
        // Primeiro, adiciona o item que está sendo montado ao carrinho
        const itemMontado = coletarItensSelecionados();
        if (itemMontado) {
            carrinhoFinal.push(itemMontado);
            renderizarCarrinhoFinal();
            document.querySelectorAll('.item-menu.selecionado').forEach(el => {
                el.classList.remove('selecionado');
            });
        }

        // Depois, chama a função para abrir o checkout
        abrirCheckout();
    });

    // Ouve o clique no botão "Voltar ao Cardápio" para fechar a tela
    btnVoltarCardapio.addEventListener('click', function() {
        telaCheckout.classList.remove('is-open');
    });

    // ================================================================ FIM
    // ================================================================ FIM

    // =================================================================
    // == LÓGICA CENTRAL PARA VALIDAR, COLETAR E ENVIAR DADOS PARA A API ==
    // =================================================================

    /**
     * @param {object} opcoes - Um objeto com opções, como { comWhatsapp: true/false }.
     */
    async function enviarPedidoFinal(opcoes = { comWhatsapp: false }) {
        const form = document.getElementById('form-checkout');
        // 1. Validação: Verifica se todos os campos obrigatórios do formulário foram preenchidos
        if (!form.checkValidity()) {
            // Se o formulário não for válido, força o navegador a mostrar as mensagens de erro padrão.
            form.reportValidity();
            return;
        }

        // 2. Coleta os dados do cliente do formulário
        const dadosCliente = {
            nome: document.getElementById('nome').value,
            telefone: document.getElementById('telefone').value,
            rua: document.getElementById('endereco-rua').value,
            numero: document.getElementById('endereco-numero').value,
            bairro: document.getElementById('endereco-bairro').value,
            referencia: document.getElementById('endereco-referencia').value,
            pagamento: document.getElementById('pagamento').value,
            observacoes: document.getElementById('observacoes').value,
            // (Futuramente, adicionaremos o 'troco_para' aqui)
        };

        // 3. Formata os dados do carrinho para enviar à API
        const carrinhoFormatado = carrinhoFinal.map(item => {
            return item.map(produto => ({ id: produto.id }));
        });

        // 4. Monta o payload completo para enviar ao Django
        const payload = {
            loja_id: lojaId,
            cliente: dadosCliente,
            carrinho: carrinhoFormatado // Enviamos a lista de IDs de produtos
        };

        try {
            // 5. Envia os dados para a API do Django
            const response = await fetch('/loja/finalizar-pedido/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();


            if (data.success) {
                carrinhoFinal = []; // Limpa o carrinho na variável
                salvarCarrinho(); // Limpa o carrinho na memória do navegador
                // 6. Se o pedido foi salvo, decide o que fazer a seguir
                if (opcoes.comWhatsapp) {

                    const mensagem = montarMensagemWhatsApp(data.pedido_id, dadosCliente, carrinhoFinal);
                    const urlWhatsapp = `https://wa.me/${lojaWhatsapp}?text=${mensagem}`;
                    window.location.href = urlWhatsapp;

                } else {
                    alert(`Pedido #${data.pedido_id} realizado com sucesso!`);
                    window.location.reload(); // Recarrega a página para um novo pedido
                }
            } else {
                alert('Ocorreu um erro ao salvar seu pedido: ' + data.error);
            }
        } catch (error) {
            console.error('Erro de rede:', error);
            alert('Falha de conexão. Não foi possível enviar seu pedido.');
        }
    }

    // ================================================================ FIM
    // ================================================================ FIM

    // =================================================================
    // == LÓGICA PARA A MENSAGEM FORMATADA NO WHATSAPP ==
    // =================================================================

    function montarMensagemWhatsApp(pedidoId, dadosCliente, carrinho) {
        let totalGeral = 0;
        let mensagem = `🎉 **NOVO PEDIDO RECEBIDO!** 🎉\n\n`;
        mensagem += `**Pedido:** #${pedidoId}\n\n`;
        mensagem += `*Cliente:*\n`;
        mensagem += `Nome: ${dadosCliente.nome}\n`;
        mensagem += `Telefone: ${dadosCliente.telefone}\n\n`;
        mensagem += `*Endereço de Entrega:*\n`;
        mensagem += `${dadosCliente.rua}, Nº ${dadosCliente.numero}, ${dadosCliente.bairro}\n`;
        if (dadosCliente.referencia) {
            mensagem += `Referência: ${dadosCliente.referencia}\n`;
        }
        mensagem += `\n**RESUMO DO PEDIDO:**\n`;

        carrinho.forEach((item, index) => {
            let subtotalItem = 0;
            mensagem += `\n*Item ${index + 1}:*\n`;

            // Encontra o 'tamanho' dentro do item
            const tamanho = item.find(p => p.categoriaNome.toLowerCase() === 'tamanhos');
            // Pega todos os outros produtos que não são 'tamanho'
            const outrosItens = item.filter(p => p.categoriaNome.toLowerCase() !== 'tamanhos');



            if (tamanho) {
                mensagem += `- ${tamanho.nome}\n`;
                subtotalItem += tamanho.preco;
            }

            outrosItens.forEach(adicional => {
                subtotalItem += adicional.preco;
                mensagem += `- ${adicional.nome}\n`;
            });
            totalGeral += subtotalItem;
        });

        if (dadosCliente.observacoes) {
            mensagem += `\n*Observações:*\n${dadosCliente.observacoes}\n`;
        }

        mensagem += `\n*Total:* *R$ ${totalGeral.toFixed(2).replace('.', ',')}*\n`;
        mensagem += `*Pagamento:* ${dadosCliente.pagamento}\n`;

        return encodeURIComponent(mensagem);
    }
    // ================================================================ FIM
    // ================================================================ FIM

    // =================================================================
    // == CONECETANDO OS BOTÕES DE CHECKOUT ==
    // =================================================================

    const btnEnviarWhatsapp = document.getElementById('btn-enviar-whatsapp');
    const btnRealizarPedidoPainel = document.getElementById('btn-realizar-pedido-painel');

    if (btnEnviarWhatsapp) {
        btnEnviarWhatsapp.addEventListener('click', function() {
            // Chama a função central com a opção de enviar para o WhatsApp
            enviarPedidoFinal({ comWhatsapp: true });
        });
    }

    if (btnRealizarPedidoPainel) {
        btnRealizarPedidoPainel.addEventListener('click', function() {
            // Chama a função central SEM a opção de WhatsApp
            enviarPedidoFinal({ comWhatsapp: false });
        });
    }
    // ================================================================ FIM
    // ================================================================ FIM

    // =================================================================
    // == LÓGICA PARA O CAMPO DINÂMICO DE TROCO ==
    // =================================================================

    // Seleciona os elementos pagamento
    const pagamentoSelect = document.getElementById('pagamento');
    const campoTrocoDiv = document.getElementById('campo-troco');

    // Adiciona um "ouvinte" para o evento de 'change' no menu dropdown
    if (pagamentoSelect) {
        pagamentoSelect.addEventListener('change', function() {
            // Verifica qual é a opção selecionada
            if (this.value === 'dinheiro') {
                // Se for 'dinheiro', mostra o campo de troco
                campoTrocoDiv.style.display = 'block';
            } else {
                // Para qualquer outra opção, esconde o campo de troco
                campoTrocoDiv.style.display = 'none';
            }
        });
    }
    // ================================================================ FIM
    // ================================================================ FIM

    carregarCarrinho();

}); // Fim do 'DOMContentLoaded'