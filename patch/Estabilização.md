Regra Monetária Baseada em Transações:
Um Mecanismo de Estabilização por Clearing para Moedas Fiat
Resumo

Este artigo propõe uma regra monetária baseada em transações na qual a oferta monetária se ajusta dinamicamente à atividade econômica doméstica medida pelo volume de transações. Diferentemente dos sistemas monetários fiat tradicionais, nos quais a expansão monetária depende de decisões discricionárias de política econômica ou da expansão do crédito, o modelo proposto vincula a criação de liquidez diretamente à atividade econômica.

A regra gera um mecanismo de estabilização endógeno em que a oferta monetária se contrai durante desacelerações econômicas e se expande durante períodos de maior volume de transações. Esse processo cria um sistema de retroalimentação que alinha a oferta monetária com a produção econômica real, potencialmente reduzindo instabilidades inflacionárias e mitigando dinâmicas de hiperinflação.

Testes de estresse por simulações Monte Carlo em cenários extremos de crise — inspirados em episódios inflacionários de países como Argentina e Venezuela — sugerem que a regra baseada em clearing reduz significativamente a volatilidade inflacionária quando comparada a regimes fiat sem restrições de emissão.

1 Introdução

Os sistemas monetários fiat modernos dependem fortemente de decisões discricionárias de política monetária, ajustes de taxa de juros e mecanismos de expansão de crédito para administrar a liquidez na economia. Embora esse modelo permita flexibilidade, ele também introduz o risco de divergência entre a oferta monetária e a atividade econômica real.

Historicamente, episódios de inflação elevada e hiperinflação estiveram associados à expansão monetária desconectada da capacidade produtiva da economia.

Este trabalho explora uma arquitetura monetária alternativa baseada em regras, na qual a oferta monetária segue a atividade de compensação de transações econômicas.

A hipótese central é que ancorar a oferta monetária na atividade econômica cria um mecanismo de retroalimentação autocorretivo capaz de estabilizar a dinâmica de preços sem necessidade de intervenção contínua da autoridade monetária.

2 A Regra Monetária Baseada em Clearing

Considere a seguinte relação fundamental:

𝐹
𝑡
=
𝐶
𝑡
𝑆
𝑡
F
t
	​

=
S
t
	​

C
t
	​

	​


onde:

𝐶
𝑡
C
t
	​

 representa a atividade econômica agregada (proxy de produção ou atividade econômica)

𝑆
𝑡
S
t
	​

 representa a oferta monetária circulante.

O ajuste de preços segue uma regra de reconvergência elástica:

𝑃
𝑎
𝑑
𝑗
=
𝑃
𝑠
𝑝
𝑒
𝑐
(
𝐹
𝑃
𝑠
𝑝
𝑒
𝑐
)
𝐾
P
adj
	​

=P
spec
	​

(
P
spec
	​

F
	​

)
K
𝑃
𝑡
=
(
1
−
𝛼
)
𝑃
𝑠
𝑝
𝑒
𝑐
+
𝛼
𝑃
𝑎
𝑑
𝑗
P
t
	​

=(1−α)P
spec
	​

+αP
adj
	​


onde:

𝑃
𝑠
𝑝
𝑒
𝑐
P
spec
	​

 representa a dinâmica especulativa de preços

𝐾
K controla a força da reconvergência ao fundamental

𝛼
α determina o grau de suavização do ajuste.

A condição de estabilidade do sistema é:

0
<
𝛼
𝐾
<
2
0<αK<2

Essa condição garante que a dinâmica de preços permaneça limitada em torno do fundamental macroeconômico.

3 Ajuste de Oferta Baseado em Transações

A atualização da oferta monetária é definida pela atividade de clearing de transações:

𝑔
𝑐
𝑙
𝑒
𝑎
𝑟
=
log
⁡
(
𝑉
𝑡
𝑉
𝑡
−
1
)
g
clear
	​

=log(
V
t−1
	​

V
t
	​

	​

)

onde 
𝑉
𝑡
V
t
	​

 representa o volume de transações.

A oferta monetária evolui segundo:

𝑆
𝑡
+
1
=
𝑆
𝑡
⋅
𝑒
𝑔
𝑐
𝑙
𝑒
𝑎
𝑟
S
t+1
	​

=S
t
	​

⋅e
g
clear
	​


Assim:

aumento da atividade econômica → expansão da oferta monetária

redução da atividade econômica → contração da oferta monetária.

Esse mecanismo vincula diretamente a criação de liquidez à atividade econômica doméstica, em vez de depender de decisões políticas ou de mercados financeiros.

4 Testes de Estresse em Cenários de Crise

Para avaliar a robustez do mecanismo, foram simulados cenários sintéticos representando crises macroeconômicas severas.

Os testes incluíram:

colapso de produção

depreciação cambial extrema

expansão de crédito

monetização fiscal

efeitos de expectativas inflacionárias.

Simulações Monte Carlo com parâmetros extremos foram executadas para avaliar a estabilidade do sistema.

Resultados resumidos

Inflação máxima mensal (mediana das simulações):

Regime	Inflação máxima
Fiat tradicional	~199%
Regra de clearing	~31%

Cenário extremo:

Regime	Inflação máxima
Fiat	
10
14
10
14
%
Clearing	~113%

Os resultados indicam que a regra baseada em clearing reduz significativamente a volatilidade inflacionária e mantém os preços mais próximos do fundamental macroeconômico.

5 Interpretação Estrutural

O mecanismo proposto pode ser interpretado como um sistema de estabilização por retroalimentação.

A dinâmica pode ser representada como:

desvio de preços
→ correção elástica
→ reconvergência ao fundamental

O parâmetro 
𝐾
K atua de maneira análoga a um ganho em sistemas de controle.

Isso cria uma força estabilizadora que impede que a dinâmica de preços se afaste indefinidamente do fundamental macroeconômico.

6 Possível Implementação de Política Monetária

Diferentemente de propostas que exigem substituição completa da moeda existente, a regra de clearing poderia ser implementada mantendo a moeda fiat atual.

Nesse arranjo:

a moeda nacional continuaria a mesma

a oferta monetária passaria a seguir uma regra baseada em atividade econômica doméstica.

Esse tipo de estrutura poderia complementar instituições de banco central existentes, adicionando um mecanismo automático de estabilização monetária.

7 Limitações

O modelo apresentado utiliza algumas simplificações importantes:

o volume de transações é tratado como proxy de atividade econômica

a dinâmica de crédito é simplificada

fatores institucionais e políticos não são considerados.

Pesquisas futuras devem incluir calibração com dados macroeconômicos reais e integração com a dinâmica do sistema financeiro.

8 Conclusão

Este artigo apresenta uma regra monetária baseada em transações capaz de alinhar a oferta monetária à atividade econômica doméstica.

Simulações indicam que esse mecanismo pode reduzir significativamente a volatilidade inflacionária e limitar dinâmicas de hiperinflação.

Investigações futuras devem explorar validação empírica com dados históricos e avaliar caminhos institucionais para implementação dessa arquitetura monetária.
