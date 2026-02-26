import { createApp, ref, onMounted } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js';
import { firestoreDocRef, auth, setDoc, onSnapshot, signInWithEmailAndPassword, signOut, onAuthStateChanged } from './firebase.js';

createApp({
    setup() {
        // Estado de Autenticação
        const currentUser = ref(null);
        const loginEmail = ref('');
        const loginPassword = ref('');
        const authError = ref('');
        const isAuthenticating = ref(true);

        // Estado da Aplicação
        const db = ref({ teams: [], roles: [], logs: [] });
        const isDark = ref(false);
        const searchQuery = ref('');
        const showModal = ref(false);
        const showLogs = ref(false);
        const unreadLogs = ref(false);
        const syncing = ref(false);
        const areas = ["Controle do Produto", "Qualitron L4", "Qualitron L5", "Qualitron 6A", "Qualitron 6B", "Inspeção", "Outros / volante"];
        const modalData = ref({ id: null, teamId: null, name: '', roleId: '', area: '' });
        
        let draggedItem = null;
        let sourceTeamId = null;
        let unsubscribeSnapshot = null;

        onMounted(() => {
            const theme = localStorage.getItem('theme');
            if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                isDark.value = true;
                document.documentElement.classList.add('dark');
            }

            if (auth) {
                onAuthStateChanged(auth, (user) => {
                    if (user) {
                        currentUser.value = user;
                        loadDatabase();
                    } else {
                        currentUser.value = null;
                        if (unsubscribeSnapshot) unsubscribeSnapshot();
                    }
                    isAuthenticating.value = false;
                });
            } else {
                isAuthenticating.value = false;
            }
        });

        const doLogin = async () => {
            authError.value = '';
            if (!loginEmail.value || !loginPassword.value) {
                authError.value = 'Preencha todos os campos.';
                return;
            }
            try {
                await signInWithEmailAndPassword(auth, loginEmail.value, loginPassword.value);
                loginEmail.value = '';
                loginPassword.value = '';
            } catch (error) {
                console.error(error);
                authError.value = 'Credenciais inválidas. Tente novamente.';
            }
        };

        const doLogout = async () => {
            if (confirm('Deseja terminar a sessão?')) {
                await signOut(auth);
            }
        };

        const loadDatabase = () => {
            if(firestoreDocRef) {
                unsubscribeSnapshot = onSnapshot(firestoreDocRef, (docSnap) => {
                    if (docSnap.exists()) {
                        db.value = docSnap.data();
                    } else {
                        db.value = {
                            teams: [ { id: 't1', title: 'Equipe 1', members: [] }, { id: 't2', title: 'Equipe 2', members: [] }, { id: 't3', title: 'Equipe 3', members: [] }, { id: 't4', title: 'Equipe 4', members: [] } ],
                            roles: [ { id: 'r1', name: 'Líder', color: '#dc2626' }, { id: 'r2', name: 'Operador', color: '#2563eb' } ],
                            logs: []
                        };
                        syncToFirebase();
                    }
                });
            }
        };

        const syncToFirebase = async () => {
            if(!firestoreDocRef || !currentUser.value) return;
            syncing.value = true;
            try {
                await setDoc(firestoreDocRef, JSON.parse(JSON.stringify(db.value)));
            } catch (error) {
                console.error("Erro ao guardar: ", error);
            } finally {
                syncing.value = false;
            }
        };

        // --- GESTÃO DE EQUIPES ---
        const addTeam = () => {
            db.value.teams.push({
                id: 't' + Date.now(),
                title: 'Nova Equipe',
                members: []
            });
            addLog(`Uma nova equipe foi criada.`);
            syncToFirebase();
        };

        const deleteTeam = (teamId) => {
            if (confirm("Tem certeza que deseja remover esta equipe inteira? Todos os colaboradores nela serão removidos do painel.")) {
                const teamName = db.value.teams.find(t => t.id === teamId)?.title || 'Equipe';
                db.value.teams = db.value.teams.filter(t => t.id !== teamId);
                addLog(`A equipe "${teamName}" foi removida.`);
                syncToFirebase();
            }
        };

        const getTeamStatus = (index) => {
            const diffDays = Math.floor((new Date().setHours(0,0,0,0) - new Date(2026, 1, 26)) / (1000 * 60 * 60 * 24));
            const isEvenDay = diffDays % 2 === 0;
            const isDayShift = new Date().getHours() >= 6 && new Date().getHours() < 18;

            const styleActiveDay = { text: 'Trabalhando (06h - 18h)', badgeColor: 'bg-green-100 text-green-800', borderColor: 'border-green-400 dark:border-green-600', icon: '☀️' };
            const styleActiveNight = { text: 'Trabalhando (18h - 06h)', badgeColor: 'bg-indigo-100 text-indigo-800', borderColor: 'border-indigo-400 dark:border-indigo-500', icon: '🌙' };
            const styleWaitingNight = { text: 'Entra hoje às 18h', badgeColor: 'bg-blue-50 text-blue-600', borderColor: 'border-gray-200 dark:border-gray-700', icon: '⏳' };
            const styleOffDay = { text: 'Folga (Trabalhou ontem)', badgeColor: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400', borderColor: 'border-gray-200 dark:border-gray-700 opacity-80', icon: '🛌' };
            const styleOff = { text: 'Apoio / Extra', badgeColor: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400', borderColor: 'border-gray-200 dark:border-gray-700 opacity-70', icon: '⚙️' };

            // Aplica a lógica 12x36 apenas nas 4 primeiras equipes
            if (index === 0) return isEvenDay ? (isDayShift ? styleActiveDay : styleOffDay) : styleOff; 
            if (index === 1) return isEvenDay ? (!isDayShift ? styleActiveNight : styleWaitingNight) : styleOff; 
            if (index === 2) return !isEvenDay ? (isDayShift ? styleActiveDay : styleOffDay) : styleOff; 
            if (index === 3) return !isEvenDay ? (!isDayShift ? styleActiveNight : styleWaitingNight) : styleOff; 
            
            // Equipes adicionais assumem status neutro de apoio
            return styleOff;
        };

        const addLog = (message) => {
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            db.value.logs.unshift({ id: Date.now(), time, message });
            if (db.value.logs.length > 50) db.value.logs.pop(); 
            if (!showLogs.value) unreadLogs.value = true;
            syncToFirebase();
        };

        const clearLogs = () => { if(confirm('Apagar histórico?')) { db.value.logs = []; syncToFirebase(); } };
        const getRoleName = (id) => (db.value.roles.find(x => x.id === id) || {}).name || '?';
        const getRoleColor = (id) => (db.value.roles.find(x => x.id === id) || {}).color || '#ccc';
        const filteredMembers = (members) => searchQuery.value ? members.filter(m => m.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || m.area.toLowerCase().includes(searchQuery.value.toLowerCase())) : members;
        const toggleTheme = () => { isDark.value = !isDark.value; localStorage.setItem('theme', isDark.value ? 'dark' : 'light'); document.documentElement.classList.toggle('dark'); };
        
        const openModal = (teamId) => { modalData.value = { id: null, teamId, name: '', roleId: db.value.roles[0]?.id, area: areas[0] }; showModal.value = true; };
        const editMember = (teamId, member) => { modalData.value = { ...member, teamId }; showModal.value = true; };
        
        const saveMember = () => {
            if (!modalData.value.name) return alert('Preencha o nome!');
            const team = db.value.teams.find(t => t.id === modalData.value.teamId);
            if (modalData.value.id) {
                const index = team.members.findIndex(m => m.id === modalData.value.id);
                const oldArea = team.members[index].area;
                team.members[index] = { ...modalData.value };
                if(oldArea !== modalData.value.area) addLog(`A área de ${modalData.value.name} mudou para ${modalData.value.area}.`);
            } else {
                team.members.push({ id: 'm' + Date.now(), name: modalData.value.name, roleId: modalData.value.roleId, area: modalData.value.area });
                addLog(`Novo colaborador: ${modalData.value.name} na ${team.title}.`);
            }
            showModal.value = false;
            syncToFirebase();
        };

        const dragStart = (e, member, teamId) => { 
            draggedItem = member; sourceTeamId = teamId; 
            setTimeout(() => e.target.classList.add('dragging'), 0); 
        };
        
        const dragEnd = (e) => { 
            e.target.classList.remove('dragging'); 
            document.querySelectorAll('.drag-over-list, .drag-over-card').forEach(el => el.classList.remove('drag-over-list', 'drag-over-card')); 
        };

        const allowDropList = (e) => { e.currentTarget.classList.add('drag-over-list'); };
        const leaveDropList = (e) => { e.currentTarget.classList.remove('drag-over-list'); };
        
        const dropOnList = (e, targetTeamId) => {
            e.currentTarget.classList.remove('drag-over-list');
            if(!draggedItem) return;

            const sourceTeam = db.value.teams.find(t => t.id === sourceTeamId);
            const targetTeam = db.value.teams.find(t => t.id === targetTeamId);
            
            if (sourceTeamId === targetTeamId) return; 

            sourceTeam.members = sourceTeam.members.filter(m => m.id !== draggedItem.id);
            targetTeam.members.push(draggedItem);
            
            addLog(`Movimentação: ${draggedItem.name} foi para ${targetTeam.title}.`);
            draggedItem = null; sourceTeamId = null;
            syncToFirebase();
        };

        const dragEnterCard = (e) => { e.currentTarget.classList.add('drag-over-card'); };
        const dragLeaveCard = (e) => { e.currentTarget.classList.remove('drag-over-card'); };
        
        const dropOnCard = (e, targetTeamId, targetMember) => {
            e.currentTarget.classList.remove('drag-over-card');
            if (!draggedItem || draggedItem.id === targetMember.id) return;

            const sourceTeam = db.value.teams.find(t => t.id === sourceTeamId);
            const targetTeam = db.value.teams.find(t => t.id === targetTeamId);
            
            sourceTeam.members = sourceTeam.members.filter(m => m.id !== draggedItem.id);
            
            const targetIndex = targetTeam.members.findIndex(m => m.id === targetMember.id);
            targetTeam.members.splice(targetIndex, 0, draggedItem);
            
            if (sourceTeamId === targetTeamId) {
                addLog(`Reordenação: Posição de ${draggedItem.name} ajustada.`);
            } else {
                addLog(`Movimentação: ${draggedItem.name} foi para ${targetTeam.title}.`);
            }
            
            draggedItem = null; sourceTeamId = null;
            syncToFirebase();
        };

        return { 
            currentUser, isAuthenticating, loginEmail, loginPassword, authError, doLogin, doLogout,
            db, isDark, searchQuery, showModal, showLogs, unreadLogs, syncing, modalData, areas, 
            getRoleName, getRoleColor, filteredMembers, toggleTheme, getTeamStatus, openModal, editMember, saveMember, 
            dragStart, dragEnd, allowDropList, leaveDropList, dropOnList, dragEnterCard, dragLeaveCard, dropOnCard, 
            syncToFirebase, clearLogs, addTeam, deleteTeam // Funções de equipe exportadas aqui
        };
    }
}).mount('#app');
