import { useState } from 'react';
import { Users, Plus, User, AlertCircle, Apple, Activity } from 'lucide-react';

export default function Household() {
  const [members, setMembers] = useState([
    {
      id: '1',
      name: 'Brandon',
      relationship: 'self',
      restrictions: [],
      nutrition: {
        daily_calories: 2200,
        daily_protein_g: 150,
      },
    },
  ]);
  const [showAddMember, setShowAddMember] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Household</h2>
          <p className="text-sm text-gray-500">Manage members, allergies, and nutrition targets</p>
        </div>
        <button
          onClick={() => setShowAddMember(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <Plus size={16} />
          Add Member
        </button>
      </div>

      {/* Household Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <Users size={20} />
            </div>
            <p className="text-sm text-gray-500">Members</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">{members.length}</p>
        </div>
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-red-50 rounded-lg text-red-600">
              <AlertCircle size={20} />
            </div>
            <p className="text-sm text-gray-500">Allergies</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {members.reduce((a, m) => a + m.restrictions.length, 0)}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-50 rounded-lg text-green-600">
              <Apple size={20} />
            </div>
            <p className="text-sm text-gray-500">Avg Calories</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {members.length > 0
              ? Math.round(members.reduce((a, m) => a + (m.nutrition?.daily_calories || 0), 0) / members.length)
              : 0}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
              <Activity size={20} />
            </div>
            <p className="text-sm text-gray-500">Nutrition Targets</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {members.filter(m => m.nutrition).length}
          </p>
        </div>
      </div>

      {/* Members List */}
      <div className="bg-white rounded-xl border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Household Members</h3>
        </div>
        <div className="divide-y">
          {members.map((member) => (
            <div key={member.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <User size={24} className="text-blue-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900">{member.name}</h4>
                      <span className="px-2 py-0.5 text-xs font-medium text-gray-500 bg-gray-100 rounded">
                        {member.relationship}
                      </span>
                    </div>
                    
                    {member.restrictions.length > 0 && (
                      <div className="flex items-center gap-2 mt-2">
                        <AlertCircle size={14} className="text-red-500" />
                        <span className="text-sm text-red-600">
                          {member.restrictions.length} dietary restriction
                          {member.restrictions.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                    )}
                    
                    {member.nutrition && (
                      <div className="mt-3 flex items-center gap-4">
                        <div className="px-3 py-1 bg-green-50 rounded-lg">
                          <p className="text-xs text-gray-500">Daily Calories</p>
                          <p className="font-semibold text-green-700">{member.nutrition.daily_calories}</p>
                        </div>
                        <div className="px-3 py-1 bg-blue-50 rounded-lg">
                          <p className="text-xs text-gray-500">Protein</p>
                          <p className="font-semibold text-blue-700">{member.nutrition.daily_protein_g}g</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Allergen Safety Panel */}
      <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle size={24} className="text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800">Allergen Safety</h3>
        </div>
        <p className="text-yellow-700 mb-4">
          The system will warn you about potential allergens based on household member profiles.
          Cross-contamination detection coming soon.
        </p>
        <div className="flex gap-2">
          <span className="px-3 py-1 text-xs font-medium bg-white rounded-full text-gray-700">
            Peanuts
          </span>
          <span className="px-3 py-1 text-xs font-medium bg-white rounded-full text-gray-700">
            Tree Nuts
          </span>
          <span className="px-3 py-1 text-xs font-medium bg-white rounded-full text-gray-700">
            Dairy
          </span>
          <span className="px-3 py-1 text-xs font-medium bg-white rounded-full text-gray-700">
            Gluten
          </span>
        </div>
      </div>

      {/* Add Member Modal (placeholder) */}
      {showAddMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-96">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Member</h3>
            <p className="text-sm text-gray-500 mb-4">
              Member creation UI coming. Use API for now:
            </p>
            <code className="block bg-gray-100 p-3 rounded text-sm">
              POST /v1/household/members
            </code>
            <button
              onClick={() => setShowAddMember(false)}
              className="mt-4 w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
